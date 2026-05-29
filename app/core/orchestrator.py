"""Stage 0~7 파이프라인 흐름 제어 (D43)."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.api.llm_client import LLMClient
from app.core import (
    stage0_dom_scan,
    stage1_ingest,
    stage2_tc_design,
    stage3_verify,
    stage5_execute,
    stage6_enhance,
    stage7_output,
)
from app.tools.excel_builder import build_review

RUNS_DIR = Path("data/runs")


@dataclass
class RunConfig:
    api_key: str
    target_url: str
    input_files: list[str] = field(default_factory=list)
    auth_sequence: list[dict] = field(default_factory=list)
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    inferred_threshold: float = 0.30
    max_leaves: int = 50
    """Stage 2에서 처리할 최대 leaf 수. 0 = 무제한.
    무료 플랜(20회/일) 기준: 50이면 약 50회 TC_DESIGN 호출 필요.
    유료 플랜이면 0으로 설정해 제한 없이 실행."""
    model_override: str | None = None
    """Contract frontmatter 모델을 이 모델로 교체. 예: 'gemini-2.5-flash'.
    None이면 각 Contract의 model 그대로 사용."""

    selected_urls: list[str] | None = None
    """페이지 선택 다이얼로그에서 선택된 URL 목록. None이면 BFS 전체."""

    cached_features: dict[str, list[dict]] | None = None
    """URL → features 캐시 (과거 run에서 복사). 해당 URL은 LLM 호출 생략."""

    max_pages: int = 30
    """BFS 최대 페이지 수 (selected_urls가 있으면 무시됨)."""

    headless_exec: bool = True
    """Stage 5 TC 실행 시 헤드리스 여부. False면 별도 Chromium 창이 떠
    사용자가 자동화 동작을 볼 수 있음 (마우스/키보드는 자동화에만 반응)."""

    slow_mo_ms: int = 0
    """Stage 5에서 액션 사이 인공 지연(ms). 헤드풀 모드에서 천천히 보기 위함."""


class Orchestrator:
    """AWT Stage 0~7 실행 제어."""

    def __init__(
        self,
        config: RunConfig,
        progress_cb: Callable[[str], None] | None = None,
        raw_progress_cb: Callable[[str], None] | None = None,
    ):
        """
        Args:
            progress_cb:     사용자 친화 메시지(humanize 후). humanize=None인 메시지는 받지 않음.
            raw_progress_cb: 원본(raw) 메시지 — humanize 전 단계. 상세 로그 패널용.
        """
        self.config = config
        # _safe_cb 위에서 이미 설정됨
        self.run_dir = RUNS_DIR / config.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        # progress_cb를 CP949 안전 + 사용자 친화적 메시지 변환 래퍼로 감쌈
        from app.core.messages import humanize

        def _safe_cb(msg: str) -> None:
            # 1) 상세 로그: 원본 메시지 그대로 전달 (필터링 없음)
            if raw_progress_cb is not None:
                try:
                    raw_progress_cb(msg)
                except UnicodeEncodeError:
                    safe = msg.encode("ascii", errors="replace").decode("ascii")
                    try:
                        raw_progress_cb(safe)
                    except Exception:
                        pass
                except Exception:
                    pass

            # 2) 사용자 친화 로그: humanize 후 전달
            friendly = humanize(msg)
            if friendly is None:          # 내부 디버그 메시지 — 사용자 화면 표시 안 함
                return
            try:
                (progress_cb or (lambda m: None))(friendly)
            except UnicodeEncodeError:
                safe = friendly.encode("ascii", errors="replace").decode("ascii")
                (progress_cb or (lambda m: None))(safe)

        self._cb = _safe_cb
        self.llm = LLMClient(
            api_key=config.api_key,
            run_id=config.run_id,
            model_override=config.model_override,
            progress_cb=self._cb,
        )
        self.tcs: list[dict] = []
        self.ingest_result: dict = {}
        self._stage = 0
        # 협력적 일시정지/중단 플래그 (UI가 set, stage5가 read)
        self._paused  = False
        self._stopped = False

    # ── 일시정지/중단 ────────────────────────────────────────────────────
    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    def is_paused(self) -> bool:
        return self._paused

    def set_stopped(self, stopped: bool) -> None:
        self._stopped = stopped

    def is_stopped(self) -> bool:
        return self._stopped

    # ── Stage 0 ──────────────────────────────────────────────────────────
    def run_stage0(self) -> dict:
        self._cb("▶ Stage 0: DOM 스캔")
        result = stage0_dom_scan.scan(
            url=self.config.target_url,
            llm_client=self.llm,
            run_dir=self.run_dir,
            auth_sequence=self.config.auth_sequence or None,
            max_pages=self.config.max_pages,
            progress_cb=self._cb,
            selected_urls=self.config.selected_urls,
            cached_features=self.config.cached_features,
        )
        self._stage = 0
        return result

    # ── Stage 1 ──────────────────────────────────────────────────────────
    def run_stage1(self, feature_spec: dict | None = None) -> dict:
        self._cb("▶ Stage 1: 파일 파싱·정규화")
        self.ingest_result = stage1_ingest.ingest(
            files=self.config.input_files,
            run_dir=self.run_dir,
            feature_spec=feature_spec,
            progress_cb=self._cb,
        )
        self._stage = 1
        return self.ingest_result

    # ── Stage 2 ──────────────────────────────────────────────────────────
    def run_stage2(self) -> list[dict]:
        self._cb("▶ Stage 2: TC 설계")
        self.tcs = stage2_tc_design.design(
            leaves=self.ingest_result["leaves"],
            manual_text=self.ingest_result["manual_text"],
            llm_client=self.llm,
            max_leaves=self.config.max_leaves,
            progress_cb=self._cb,
        )
        self._save_intermediate("tc_raw")
        self._stage = 2
        return self.tcs

    # ── Stage 2 이후 TC 수 검사 ──────────────────────────────────────────
    def _assert_tcs_not_empty(self, stage_name: str) -> None:
        """TC 목록이 비어있으면 명확한 메시지로 중단."""
        if not self.tcs:
            raise RuntimeError(
                f"{stage_name}: TC가 0개입니다.\n"
                "가능한 원인:\n"
                "  1) 대상 URL에 접근 실패 (Stage 0 DOM 스캔 결과 없음)\n"
                "  2) 매뉴얼 파일 없음 + DOM 기능도 0개 추출\n"
                "  3) LLM API 오류로 모든 leaf 분석 실패 (Gemini 안전 필터/일일 쿼터 등)\n"
                "  4) Stage 2 첫 호출이 빈 응답으로 차단됨 (RECITATION/SAFETY)\n"
                "로그에서 '기능 분석 실패' / '안전 필터' 메시지를 확인하세요."
            )

    # ── Stage 3 ──────────────────────────────────────────────────────────
    def run_stage3(self) -> list[dict]:
        self._cb("▶ Stage 3: V1~V5 검증")
        self._assert_tcs_not_empty("Stage 3")
        self.tcs = stage3_verify.verify(
            tcs=self.tcs,
            manual_text=self.ingest_result["manual_text"],
            llm_client=self.llm,
            leaves=self.ingest_result["leaves"],
            inferred_threshold=self.config.inferred_threshold,
            progress_cb=self._cb,
        )
        self._save_intermediate("tc_verified")
        # Reviewer Gate용 Excel 생성 (TC 있을 때만)
        if self.tcs:
            build_review(self.tcs, self.run_dir / "tc_review.xlsx")
        self._stage = 3
        return self.tcs

    # ── Stage 4 (UI) ─────────────────────────────────────────────────────
    def apply_gate_decisions(self, decisions: dict[str, dict]) -> list[dict]:
        """UI에서 받은 A/E/R/P 결정을 TC에 반영."""
        self._cb("▶ Stage 4: Reviewer Gate 반영")
        for tc in self.tcs:
            d = decisions.get(tc["tc_id"])
            if d:
                tc["review_status"] = d.get("status", tc["review_status"])
                tc["reviewer_note"] = d.get("note", "")
                tc["reviewer_id"] = d.get("reviewer_id", "")
        self._save_intermediate("tc_gated")
        self._stage = 4
        return self.tcs

    # ── Stage 5 ──────────────────────────────────────────────────────────
    def run_stage5(self) -> list[dict]:
        self._cb("▶ Stage 5: Playwright 자동 실행")
        # 시작 전 플래그 리셋 (이전 실행이 중단된 상태일 수 있음)
        self._paused  = False
        self._stopped = False
        self.tcs = stage5_execute.execute(
            tcs=self.tcs,
            base_url=self.config.target_url,
            auth_sequence=self.config.auth_sequence or None,
            progress_cb=self._cb,
            headless=self.config.headless_exec,
            slow_mo_ms=self.config.slow_mo_ms,
            is_paused=self.is_paused,
            is_stopped=self.is_stopped,
        )
        self._save_intermediate("tc_executed")
        self._stage = 5
        return self.tcs

    # ── Stage 6 ──────────────────────────────────────────────────────────
    def run_stage6(self) -> list[dict]:
        self._cb("▶ Stage 6: 실패 원인 분석")
        self.tcs = stage6_enhance.enhance(
            tcs=self.tcs,
            llm_client=self.llm,
            progress_cb=self._cb,
        )
        self._stage = 6
        return self.tcs

    # ── Stage 7 ──────────────────────────────────────────────────────────
    def run_stage7(self) -> Path:
        self._cb("▶ Stage 7: Excel 최종 산출")
        out = stage7_output.output(
            tcs=self.tcs,
            run_dir=self.run_dir,
            progress_cb=self._cb,
        )
        self._stage = 7
        return out

    # ── 편의 메서드 ─────────────────────────────────────────────────────
    def run_pipeline(
        self,
        skip_stage0: bool = False,
        gate_decisions: dict | None = None,
    ) -> Path:
        """Stage 0~7 전체 실행 (Stage 4 결정은 gate_decisions로 주입)."""
        feature_spec = None
        if not skip_stage0:
            feature_spec = self.run_stage0()

        self.run_stage1(feature_spec)
        self.run_stage2()
        self.run_stage3()
        self.apply_gate_decisions(gate_decisions or {})
        self.run_stage5()
        self.run_stage6()
        return self.run_stage7()

    def load_from_stage3(self, run_id: str | None = None) -> bool:
        """기존 tc_verified.json 로드 — Stage 4부터 재개할 때 사용.

        Args:
            run_id: 불러올 run ID. None이면 self.config.run_id 사용.
        Returns:
            True if loaded successfully, False otherwise.
        """
        import json
        target_run = run_id or self.config.run_id
        path = RUNS_DIR / target_run / "tc_verified.json"
        if not path.exists():
            return False
        self.tcs = json.loads(path.read_text(encoding="utf-8"))
        # ingest_result 복원: manual.txt 에서 재파싱
        manual_path = RUNS_DIR / target_run / "ingest" / "manual.txt"
        if manual_path.exists():
            manual_text = manual_path.read_text(encoding="utf-8")
            from app.core import stage1_ingest
            leaves = stage1_ingest._extract_leaves_from_text(manual_text)
            self.ingest_result = {"manual_text": manual_text, "leaves": leaves}
        self.run_dir = RUNS_DIR / target_run
        self._stage = 3
        return True

    def _save_intermediate(self, name: str) -> None:
        import json
        path = self.run_dir / f"{name}.json"
        path.write_text(
            json.dumps(self.tcs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
