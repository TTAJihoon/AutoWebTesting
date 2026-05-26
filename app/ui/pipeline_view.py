"""파이프라인 실행 진행 창 — Stage 0~7 실시간 로그 (D45: PySide6)."""
from __future__ import annotations
import json
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QPlainTextEdit, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QStatusBar,
)

from app.core.orchestrator import Orchestrator, RunConfig
from app.ui.theme import pill_btn, utility_btn

# 기법 한글 변환 (DESIGN.md 사용자 선택 기준)
_TECHNIQUE_KO: dict[str, str] = {
    "happy_path":       "정상 흐름",
    "negative_basic":   "오류 기본",
    "negative_deep":    "오류 심층",
    "boundary":         "경계값 분석",
    "equivalence":      "동등 분할",
    "state_transition": "상태 전이",
    "cross_feature":    "기능 간 연계",
}

# 상태(review_status) 한글 변환
_STATUS_KO: dict[str, str] = {
    "pending":  "보류",
    "approved": "승인",
    "edited":   "수정",
    "rejected": "거부",
}

# 실행 결과(result) 한글 변환
_RESULT_KO: dict[str, str] = {
    "not_executed": "미실행",
    "pass":         "통과",
    "fail":         "실패",
    "blocked":      "차단",
}


class _PreGateWorker(QThread):
    """Stage 0~3 백그라운드 실행."""
    stage_done = Signal(int)
    finished = Signal(list)   # verified tcs
    error = Signal(str)

    def __init__(self, orch: Orchestrator, has_files: bool):
        super().__init__()
        self._orch = orch
        self._has_files = has_files

    def run(self) -> None:
        try:
            feature_spec = None
            if not self._has_files:
                feature_spec = self._orch.run_stage0()
                self.stage_done.emit(1)
            self._orch.run_stage1(feature_spec)
            self.stage_done.emit(2)
            self._orch.run_stage2()
            self.stage_done.emit(3)
            tcs = self._orch.run_stage3()
            self.stage_done.emit(4)
            self.finished.emit(tcs)
        except Exception:
            self.error.emit(traceback.format_exc())


class _PostGateWorker(QThread):
    """Stage 5~7 백그라운드 실행."""
    stage_done = Signal(int)
    finished = Signal(object)  # Path
    error = Signal(str)

    def __init__(self, orch: Orchestrator):
        super().__init__()
        self._orch = orch

    def run(self) -> None:
        try:
            self._orch.run_stage5()
            self.stage_done.emit(5)
            self._orch.run_stage6()
            self.stage_done.emit(6)
            out = self._orch.run_stage7()
            self.stage_done.emit(7)
            self.finished.emit(out)
        except Exception:
            self.error.emit(traceback.format_exc())


class PipelineView(QMainWindow):
    """파이프라인 실행 창. gate_decisions 주입으로 Stage 4 반영."""

    gate_review_requested = Signal(list)
    _log_signal = Signal(str)   # 워커 스레드에서 UI로 안전하게 로그 전달

    def __init__(self, config: RunConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"AWT 실행 — {config.run_id}")
        self.resize(1000, 660)
        self._config = config
        self._orch = Orchestrator(config, progress_cb=self._log_signal.emit)
        self._pre_worker: _PreGateWorker | None = None
        self._post_worker: _PostGateWorker | None = None
        self._tcs: list[dict] = []
        self._build_ui()
        # 시그널 → UI 연결 (워커 스레드에서 emit해도 안전)
        self._log_signal.connect(self._append_log)
        self._write_meta("started")

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        # 상단 정보
        info_row = QHBoxLayout()
        url_lbl = QLabel(f"대상: {self._config.target_url}")
        url_lbl.setStyleSheet("font-weight:bold;")
        info_row.addWidget(url_lbl)
        info_row.addStretch()
        self._run_btn = QPushButton("Stage 1~3 실행")
        self._run_btn.setStyleSheet(
            pill_btn(bg="#1a7a3c", bg_hover="#15803d", bg_pressed="#0f6030",
                     bg_disabled="#86efac", fg_disabled="#ffffff")
        )
        self._run_btn.clicked.connect(self._start_pre_gate)
        info_row.addWidget(self._run_btn)
        root.addLayout(info_row)

        # 진행 바 (Stage N/7)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 7)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("Stage %v / 7")
        root.addWidget(self._progress_bar)

        # 로딩 표시 — 동작 중일 때만 표시되는 얇은 indeterminate 바
        self._busy_bar = QProgressBar()
        self._busy_bar.setRange(0, 0)       # indeterminate 애니메이션
        self._busy_bar.setFixedHeight(4)
        self._busy_bar.setTextVisible(False)
        self._busy_bar.setStyleSheet(
            "QProgressBar{border:none;background:#e5e7eb;border-radius:2px;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:2px;}"
        )
        self._busy_bar.setVisible(False)
        root.addWidget(self._busy_bar)

        # 스플리터: 로그 | TC 테이블
        splitter = QSplitter(Qt.Horizontal)

        # 로그
        log_widget = QWidget()
        log_lay = QVBoxLayout(log_widget)
        log_lay.setContentsMargins(0, 0, 0, 0)
        log_lay.addWidget(QLabel("실행 로그"))
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        log_lay.addWidget(self._log)
        splitter.addWidget(log_widget)

        # TC 테이블
        tc_widget = QWidget()
        tc_lay = QVBoxLayout(tc_widget)
        tc_lay.setContentsMargins(0, 0, 0, 0)
        tc_lay.addWidget(QLabel("생성된 TC"))
        self._tc_table = QTableWidget(0, 7)
        self._tc_table.setHorizontalHeaderLabels(
            ["TC ID", "시나리오", "입력값", "예상값", "기법", "상태", "결과"]
        )
        hdr = self._tc_table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)   # 시나리오
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)   # 입력값
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)   # 예상값
        hdr.setDefaultSectionSize(90)
        self._tc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        tc_lay.addWidget(self._tc_table)

        self._gate_btn = QPushButton("Stage 4: Reviewer Gate →")
        self._gate_btn.setEnabled(False)
        self._gate_btn.setStyleSheet(
            utility_btn(bg="#5e35b1", bg_hover="#4527a0")
        )
        self._gate_btn.clicked.connect(self._open_gate)
        tc_lay.addWidget(self._gate_btn)

        self._exec_btn = QPushButton("Stage 5~7 실행")
        self._exec_btn.setEnabled(False)
        self._exec_btn.setStyleSheet(
            pill_btn(bg_disabled="#93c5fd", fg_disabled="#ffffff")
        )
        self._exec_btn.clicked.connect(self._start_post_gate)
        tc_lay.addWidget(self._exec_btn)
        splitter.addWidget(tc_widget)

        splitter.setSizes([380, 600])
        root.addWidget(splitter)

        self.setStatusBar(QStatusBar())

    # ── Stage 1~3 (Pre-Gate) ─────────────────────────────────────────────
    def _start_pre_gate(self) -> None:
        self._run_btn.setEnabled(False)
        self._log.clear()
        self._progress_bar.setValue(0)
        self._busy_bar.setVisible(True)
        self._append_log("Stage 1~3 시작...")

        self._pre_worker = _PreGateWorker(
            orch=self._orch,
            has_files=bool(self._config.input_files),
        )
        self._pre_worker.stage_done.connect(self._progress_bar.setValue)
        self._pre_worker.finished.connect(self._on_pre_gate_done)
        self._pre_worker.error.connect(self._on_error)
        self._pre_worker.start()

    def _on_pre_gate_done(self, tcs: list) -> None:
        self._tcs = tcs
        self._refresh_tc_table()
        self._gate_btn.setEnabled(True)
        self._busy_bar.setVisible(False)
        self._write_meta("stage3_done")
        self._append_log(f"Stage 3 완료 - TC {len(tcs)}개. Reviewer Gate를 진행하세요.")
        self.statusBar().showMessage(f"Stage 3 완료 - TC {len(tcs)}개")

    # ── Stage 4 Gate ─────────────────────────────────────────────────────
    def _open_gate(self) -> None:
        self.gate_review_requested.emit(self._tcs)

    def apply_gate(self, decisions: dict) -> None:
        """ReviewerGate 결정 완료 시 호출됨."""
        self._tcs = self._orch.apply_gate_decisions(decisions)
        self._refresh_tc_table()
        self._exec_btn.setEnabled(True)
        self._gate_btn.setEnabled(False)
        self._write_meta("stage4_done")
        self._append_log("Gate 결정 반영 완료. Stage 5~7을 실행하세요.")

    # ── Stage 5~7 (Post-Gate) ─────────────────────────────────────────────
    def _start_post_gate(self) -> None:
        self._exec_btn.setEnabled(False)
        self._busy_bar.setVisible(True)
        self._append_log("Stage 5~7 시작...")

        self._post_worker = _PostGateWorker(orch=self._orch)
        self._post_worker.stage_done.connect(self._progress_bar.setValue)
        self._post_worker.finished.connect(self._on_post_gate_done)
        self._post_worker.error.connect(self._on_error)
        self._post_worker.start()

    def _on_post_gate_done(self, out: Path) -> None:
        self._tcs = self._orch.tcs
        self._refresh_tc_table()
        self._busy_bar.setVisible(False)
        self._write_meta("done")
        self._append_log(f"완료 -> {out}")
        self.statusBar().showMessage(f"완료: {out.name}")

        passed = sum(1 for tc in self._tcs if tc.get("result") == "pass")
        failed = sum(1 for tc in self._tcs if tc.get("result") == "fail")
        total = len(self._tcs)
        QMessageBox.information(
            self, "실행 완료",
            f"tc_final.xlsx 생성 완료\n\n"
            f"총 {total}개  PASS {passed}  FAIL {failed}\n\n{out}"
        )

    # ── 오류 처리 ────────────────────────────────────────────────────────
    def _on_error(self, msg: str) -> None:
        self._run_btn.setEnabled(True)
        self._busy_bar.setVisible(False)
        self._append_log(f"[오류]\n{msg}")
        self.statusBar().showMessage("오류 발생")
        QMessageBox.critical(self, "오류", msg[:800])

    # ── UI 갱신 ──────────────────────────────────────────────────────────
    def _append_log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self._log.appendPlainText(line)
        # 자동 스크롤
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.statusBar().showMessage(msg[:80])

    def _refresh_tc_table(self) -> None:
        self._tc_table.setRowCount(0)
        status_colors = {
            "approved": QColor("#d1fae5"),
            "edited": QColor("#dbeafe"),
            "rejected": QColor("#fee2e2"),
            "pending": QColor("#fef9c3"),
        }
        result_colors = {
            "pass": QColor("#d1fae5"),
            "fail": QColor("#fee2e2"),
            "blocked": QColor("#ffe4e6"),
            "not_executed": QColor("#f3f4f6"),
        }
        for tc in self._tcs:
            r = self._tc_table.rowCount()
            self._tc_table.insertRow(r)

            technique_en = tc.get("design_technique", "")
            technique_ko = _TECHNIQUE_KO.get(technique_en, technique_en)
            status   = tc.get("review_status", "pending")
            result   = tc.get("result", "not_executed")

            bg       = status_colors.get(status, QColor("white"))
            res_bg   = result_colors.get(result, QColor("white"))

            status_ko = _STATUS_KO.get(status, status)
            result_ko = _RESULT_KO.get(result, result)

            cells = [
                (0, tc.get("tc_id", ""),                   bg),
                (1, tc.get("scenario", ""),                bg),
                (2, tc.get("precondition", "")[:80],       bg),
                (3, tc.get("expected", "")[:80],           bg),
                (4, technique_ko,                          bg),
                (5, status_ko,                             bg),
                (6, result_ko,                             res_bg),
            ]
            for col, text, color in cells:
                item = QTableWidgetItem(text)
                item.setBackground(color)
                self._tc_table.setItem(r, col, item)

    # ── 메타 저장 (대시보드 이력용) ───────────────────────────────────────
    def _write_meta(self, stage: str) -> None:
        try:
            meta = {
                "run_id": self._config.run_id,
                "target_url": self._config.target_url,
                "stage": stage,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            (self._orch.run_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass
