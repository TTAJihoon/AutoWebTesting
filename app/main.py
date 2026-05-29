"""AWT 진입점 — PySide6 앱 초기화 및 창 연결 (D45, D46)."""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.auth.db_client import DBClient
from app.config.db_config import DBConfig
from app.config.settings import load_api_key, get_active_provider
from app.ui.login_window import LoginWindow
from app.ui.dashboard import Dashboard
from app.ui.wizard import RunWizard
from app.ui.pipeline_view import PipelineView
from app.ui.reviewer_gate import ReviewerGate
from app.ui.theme import APPLE_QSS


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("AWT")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    app.setStyleSheet(APPLE_QSS)

    # DB 설정
    db_cfg = DBConfig.from_env()
    db = DBClient(db_cfg)

    # ── 로그인 ────────────────────────────────────────────────────────────
    login = LoginWindow(db_config=db_cfg)

    token: str = ""
    username: str = ""
    api_key: str = ""
    role: str = "reviewer"

    def _on_logged_in(t: str, u: str, k: str) -> None:
        nonlocal token, username, api_key
        token, username, api_key = t, u, k
        session_info = db.validate_session(t)
        nonlocal role
        role = session_info["role"] if session_info else "reviewer"

    login.logged_in.connect(_on_logged_in)
    if login.exec() != LoginWindow.Accepted:
        sys.exit(0)

    # ── 대시보드 ──────────────────────────────────────────────────────────
    _pipeline_views: list[PipelineView] = []
    dash: Dashboard | None = None

    def _make_dashboard() -> None:
        nonlocal dash
        dash = Dashboard(token=token, username=username, role=role, api_key=api_key, db=db)
        dash.new_run_requested.connect(_open_wizard)
        dash.open_run_requested.connect(_reopen_run)
        dash.clone_run_requested.connect(_clone_run)
        dash.resume_run_requested.connect(_resume_run)
        dash.logout_requested.connect(_do_logout)
        dash.show()

    def _resume_run(run_id: str, from_stage: int) -> None:
        """이력에서 우클릭 → 'Stage N부터 재개'.

        from_stage:
          4 = Reviewer Gate부터 (tc_verified.json 로드)
          5 = Stage 5~7부터 (tc_gated.json 로드)
        """
        import json
        from app.core.orchestrator import RunConfig
        from pathlib import Path as _P

        run_dir = _P("data/runs") / run_id
        meta_path = run_dir / "meta.json"
        if not meta_path.exists():
            QMessageBox.warning(dash, "재개 불가", f"meta.json이 없습니다: {run_id}")
            return
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            QMessageBox.critical(dash, "재개 오류", f"meta.json 로드 실패: {e}")
            return

        current_key = load_api_key() or api_key
        # 기존 meta에서 환경 복원
        cfg = RunConfig(
            api_key=current_key,
            target_url=meta.get("target_url", ""),
            input_files=meta.get("input_files") or [],
            auth_sequence=[],   # 인증은 이미 Stage 0에서 완료, 재개에선 불필요
            run_id=run_id,      # 같은 run_id 유지 — 산출물 덮어쓰기
            inferred_threshold=meta.get("inferred_threshold", 0.30),
            max_leaves=meta.get("max_leaves", 50),
            model_override=meta.get("model_override"),
            max_pages=meta.get("max_pages", 30),
            headless_exec=meta.get("headless_exec", True),
            slow_mo_ms=meta.get("slow_mo_ms", 0),
        )

        pv = PipelineView(config=cfg, parent=None)
        _pipeline_views.append(pv)

        def _open_gate(tcs: list[dict]) -> None:
            try:
                manual_text = ""
                try:
                    manual_text = pv._orch.ingest_result.get("manual_text", "")
                except Exception:
                    pass
                gate = ReviewerGate(
                    tcs=tcs, reviewer_id=username, parent=pv,
                    llm_client=pv._orch.llm,
                    manual_text=manual_text,
                )
                gate.decisions_ready.connect(pv.apply_gate)
                gate.tcs_regenerated.connect(_on_tcs_regenerated_resume)
                gate.raise_()
                gate.activateWindow()
                gate.exec()
            except Exception:
                import traceback
                QMessageBox.critical(pv, "Stage 4 오류", traceback.format_exc()[:1200])

        def _on_tcs_regenerated_resume(new_tcs: list[dict]) -> None:
            pv._tcs = new_tcs
            pv._orch.tcs = new_tcs
            pv._orch._save_intermediate("tc_verified")
            pv._refresh_tc_table()
            pv._append_log(f"🔄 거부 TC 재생성 — 총 {len(new_tcs)}개 (검토 후 다시 확정)")

        pv.gate_review_requested.connect(_open_gate)
        pv.show()

        # 재개 — orchestrator에 데이터 로드 + 적절한 stage 활성화
        try:
            if from_stage == 4:
                if not pv._orch.load_from_stage3(run_id=run_id):
                    QMessageBox.warning(pv, "재개 실패", "tc_verified.json 로드 실패")
                    return
                pv._tcs = pv._orch.tcs
                pv._max_progress = 3
                pv._update_circles(4, "Stage 4 — Reviewer Gate 대기")
                pv._set_status(f"Stage 3 완료 (재개)  |  TC {len(pv._tcs)}개", active=True, running=False)
                pv._run_btn.setVisible(False)
                pv._gate_btn.setVisible(True)
                pv._gate_btn.setEnabled(True)
                pv._exec_btn.setVisible(True)
                pv._exec_btn.setEnabled(False)
                pv._refresh_tc_table()
                # Stage 0 산출물 있으면 다운로드 버튼 노출
                if (pv._orch.run_dir / "dom-scan" / "feature-spec-draft.json").exists():
                    pv._feature_dl_btn.setVisible(True)
                    pv._feature_csv_btn.setVisible(True)
                if (pv._orch.run_dir / "dom-scan" / "screenshots").exists():
                    pv._screenshot_dir_btn.setVisible(True)
                pv._append_log(f"🔄 Stage 4부터 재개 — TC {len(pv._tcs)}개 로드됨")
            elif from_stage == 5:
                if not pv._orch.load_from_stage4(run_id=run_id):
                    QMessageBox.warning(pv, "재개 실패", "tc_gated.json 로드 실패")
                    return
                pv._tcs = pv._orch.tcs
                pv._max_progress = 4
                pv._update_circles(5, "Stage 5 대기 (재개)")
                pv._set_status(f"Stage 4 완료 (재개)  |  TC {len(pv._tcs)}개", active=True, running=False)
                pv._run_btn.setVisible(False)
                pv._gate_btn.setVisible(False)
                pv._exec_btn.setVisible(True)
                pv._exec_btn.setEnabled(True)
                pv._exec_btn.setText("Stage 5~7 실행")
                pv._refresh_tc_table()
                if (pv._orch.run_dir / "dom-scan" / "feature-spec-draft.json").exists():
                    pv._feature_dl_btn.setVisible(True)
                    pv._feature_csv_btn.setVisible(True)
                if (pv._orch.run_dir / "dom-scan" / "screenshots").exists():
                    pv._screenshot_dir_btn.setVisible(True)
                pv._append_log(f"🔄 Stage 5부터 재개 — TC {len(pv._tcs)}개 로드됨 (Gate 결정 보존)")
            else:
                QMessageBox.warning(pv, "재개 실패", f"지원하지 않는 stage: {from_stage}")
        except Exception as e:
            import traceback
            QMessageBox.critical(pv, "재개 오류", traceback.format_exc()[:1200])

    def _open_wizard() -> None:
        # 설정 탭에서 키를 저장한 경우를 위해 항상 최신값 로드
        current_key = load_api_key() or api_key
        if not current_key or current_key.startswith("AIza여기에") or current_key.startswith("sk-ant-여기에") or current_key.startswith("sk-여기에"):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                dash, "API Key 미설정",
                "LLM API Key가 설정되지 않았습니다.\n"
                "대시보드 → 설정 탭에서 API Key를 먼저 저장해주세요."
            )
            return
        wiz = RunWizard(api_key=current_key, parent=dash)
        wiz.run_config_ready.connect(_start_pipeline)
        wiz.exec()

    def _start_pipeline(config) -> None:
        pv = PipelineView(config=config, parent=None)
        _pipeline_views.append(pv)

        def _open_gate(tcs: list[dict]) -> None:
            try:
                manual_text = ""
                try:
                    manual_text = pv._orch.ingest_result.get("manual_text", "")
                except Exception:
                    pass
                gate = ReviewerGate(
                    tcs=tcs, reviewer_id=username, parent=pv,
                    llm_client=pv._orch.llm,
                    manual_text=manual_text,
                )
                gate.decisions_ready.connect(pv.apply_gate)
                # 재생성된 TC를 pipeline_view에도 반영
                gate.tcs_regenerated.connect(_on_tcs_regenerated)
                gate.raise_()
                gate.activateWindow()
                gate.exec()
            except Exception:
                import traceback
                QMessageBox.critical(
                    pv, "Stage 4 오류",
                    traceback.format_exc()[:1200],
                )

        def _on_tcs_regenerated(new_tcs: list[dict]) -> None:
            """ReviewerGate에서 재생성 발생 시 pipeline_view와 orchestrator도 동기화."""
            pv._tcs = new_tcs
            pv._orch.tcs = new_tcs
            pv._orch._save_intermediate("tc_verified")  # 중간 저장 (이후 재개 가능)
            pv._refresh_tc_table()
            pv._append_log(f"🔄 거부 TC 재생성 — 총 {len(new_tcs)}개 (검토 후 다시 확정)")

        pv.gate_review_requested.connect(_open_gate)
        pv.show()

    def _reopen_run(run_id: str) -> None:
        """이력 더블클릭 — 진행 중이면 PipelineView 포커스, 완료면 Excel 열기."""
        # ① 열려 있는 PipelineView 탐색 (최소화 상태도 포함)
        for pv in _pipeline_views:
            if (hasattr(pv, "config")
                    and pv.config.run_id == run_id
                    and not pv.isHidden()):
                if pv.isMinimized():
                    pv.showNormal()
                pv.raise_()
                pv.activateWindow()
                return

        # ② 완료된 실행 — tc_final.xlsx 열기
        run_dir = Path("data/runs") / run_id
        tc_final = run_dir / "tc_final.xlsx"
        if tc_final.exists():
            import subprocess
            subprocess.Popen(["explorer", str(tc_final)])
            return

        # ③ 진행 중도 아니고 완료도 아닌 경우 (중단된 실행 등)
        tc_verified = run_dir / "tc_verified.json"
        stage_hint = ""
        if tc_verified.exists():
            stage_hint = "Stage 3까지 완료된 실행입니다.\n"
        elif (run_dir / "tc_raw.json").exists():
            stage_hint = "Stage 2까지 완료된 실행입니다.\n"

        QMessageBox.information(
            dash, "실행 정보",
            f"Run ID: {run_id}\n"
            f"{stage_hint}"
            "열려 있는 Pipeline View가 없고 최종 Excel도 없습니다.\n"
            "새 실행을 시작하거나 우클릭 → 복제로 재실행하세요.",
        )

    def _clone_run(url: str) -> None:
        """이력 우클릭 → 복제: URL 클립보드 복사 + wizard prefill."""
        current_key = load_api_key() or api_key
        if not current_key or current_key.startswith("AIza여기에") or current_key.startswith("sk-ant-여기에") or current_key.startswith("sk-여기에"):
            QMessageBox.warning(
                dash, "API Key 미설정",
                "LLM API Key가 설정되지 않았습니다.\n"
                "대시보드 → 설정 탭에서 API Key를 먼저 저장해주세요."
            )
            return
        wiz = RunWizard(api_key=current_key, prefill_url=url, parent=dash)
        wiz.run_config_ready.connect(_start_pipeline)
        wiz.exec()

    def _do_logout() -> None:
        """로그아웃 → 대시보드 닫고 로그인 화면 재표시."""
        nonlocal token, username, api_key, role, dash
        if dash:
            dash.close()
            dash = None
        new_login = LoginWindow(db_config=db_cfg)
        new_login.logged_in.connect(_on_logged_in)
        if new_login.exec() == LoginWindow.Accepted:
            _make_dashboard()
        else:
            app.quit()

    _make_dashboard()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
