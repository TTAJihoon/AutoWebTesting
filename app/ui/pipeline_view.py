"""파이프라인 실행 진행 창 — Stage 0~7 실시간 로그 (D45: PySide6)."""
from __future__ import annotations
import json
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QPlainTextEdit,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QStatusBar, QFileDialog,
)

from app.core.orchestrator import Orchestrator, RunConfig
from app.ui.theme import pill_btn

# ── 한글 변환 테이블 ──────────────────────────────────────────────────────────
_TECHNIQUE_KO: dict[str, str] = {
    "happy_path":       "정상 흐름",
    "negative_basic":   "오류 기본",
    "negative_deep":    "오류 심층",
    "boundary":         "경계값 분석",
    "equivalence":      "동등 분할",
    "state_transition": "상태 전이",
    "cross_feature":    "기능 간 연계",
}

_STATUS_KO: dict[str, str] = {
    "pending":  "검토 전",
    "approved": "승인",
    "edited":   "수정",
    "rejected": "거부",
}

_RESULT_KO: dict[str, str] = {
    "not_executed": "실행 전",
    "pass":         "통과",
    "fail":         "실패",
    "blocked":      "차단",
}

# ── Stage 원형 스타일 ─────────────────────────────────────────────────────────
_CIRCLE_DONE = (
    "QLabel { background-color: #3b82f6; color: #ffffff;"
    " border-radius: 16px; font-size: 13px; font-weight: 700; border: none; }"
)
_CIRCLE_CURRENT = (
    "QLabel { background-color: #ffffff; color: #3b82f6;"
    " border-radius: 16px; border: 3px solid #3b82f6;"
    " font-size: 13px; font-weight: 700; }"
)
_CIRCLE_FUTURE = (
    "QLabel { background-color: #f8fafc; color: #94a3b8;"
    " border-radius: 16px; border: 2px solid #cbd5e1;"
    " font-size: 13px; font-weight: 700; }"
)
_LINE_DONE    = "QFrame { background-color: #3b82f6; border: none; }"
_LINE_PENDING = "QFrame { background-color: #e2e8f0; border: none; }"

# ── 카드 공통 스타일 ──────────────────────────────────────────────────────────
_CARD = (
    "QFrame { background-color: #ffffff; border-radius: 8px;"
    " border: 1px solid #e2e8f0; }"
)


# ─────────────────────────────────────────────────────────────────────────────
# Worker threads
# ─────────────────────────────────────────────────────────────────────────────

class _PreGateWorker(QThread):
    """Stage 0~3 백그라운드 실행."""
    stage_done = Signal(int)
    finished   = Signal(list)
    error      = Signal(str)

    def __init__(self, orch: Orchestrator, has_files: bool):
        super().__init__()
        self._orch      = orch
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
    finished   = Signal(object)   # Path
    error      = Signal(str)

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


# ─────────────────────────────────────────────────────────────────────────────
# PipelineView
# ─────────────────────────────────────────────────────────────────────────────

class PipelineView(QMainWindow):
    """파이프라인 실행 창."""

    gate_review_requested = Signal(list)
    _log_signal = Signal(str)

    @property
    def config(self) -> RunConfig:
        """main.py에서 run_id 접근용 (pv.config.run_id)."""
        return self._config

    def __init__(self, config: RunConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"AWT 실행 — {config.run_id}")
        self.resize(1120, 720)
        self._config      = config
        self._orch        = Orchestrator(config, progress_cb=self._log_signal.emit)
        self._pre_worker:  _PreGateWorker | None = None
        self._post_worker: _PostGateWorker | None = None
        self._tcs: list[dict] = []

        self._build_ui()
        self._log_signal.connect(self._append_log)
        self._write_meta("started")

    # ── UI 구성 ───────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        central.setStyleSheet("QWidget#central { background-color: #f1f5f9; }")
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── 상단 바 ──────────────────────────────────────────────────────────
        top_card = QFrame()
        top_card.setStyleSheet(_CARD)
        top_card.setFixedHeight(52)
        top_lay = QHBoxLayout(top_card)
        top_lay.setContentsMargins(16, 0, 16, 0)

        url_lbl = QLabel(f"대상 URL :  {self._config.target_url}")
        url_lbl.setStyleSheet(
            "QLabel { background: transparent; border: none;"
            " font-size: 14px; font-weight: 500; color: #1e293b; }"
        )
        top_lay.addWidget(url_lbl)
        top_lay.addStretch()

        cur_lbl = QLabel("현재 진행")
        cur_lbl.setStyleSheet(
            "QLabel { background: transparent; border: none;"
            " font-size: 12px; font-weight: 600; color: #64748b; }"
        )
        top_lay.addWidget(cur_lbl)

        self._stage_badge = QLabel("준비 중")
        self._stage_badge.setStyleSheet(
            "QLabel { background-color: #eff6ff; color: #1d4ed8;"
            " border: 1px solid #bfdbfe; border-radius: 6px;"
            " padding: 4px 14px; font-size: 13px; font-weight: 700; }"
        )
        top_lay.addWidget(self._stage_badge)
        root.addWidget(top_card)

        # ── Stage 진행 원형 표시기 ────────────────────────────────────────────
        prog_card = QFrame()
        prog_card.setStyleSheet(_CARD)
        prog_card.setFixedHeight(64)
        prog_lay = QHBoxLayout(prog_card)
        prog_lay.setContentsMargins(32, 0, 32, 0)

        self._circles: list[QLabel] = []
        self._lines:   list[QFrame] = []

        for i in range(1, 8):
            circle = QLabel(str(i))
            circle.setAlignment(Qt.AlignCenter)
            circle.setFixedSize(32, 32)
            circle.setStyleSheet(_CIRCLE_FUTURE)
            self._circles.append(circle)
            prog_lay.addWidget(circle)
            if i < 7:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFixedHeight(4)
                line.setStyleSheet(_LINE_PENDING)
                self._lines.append(line)
                prog_lay.addWidget(line, 1)

        root.addWidget(prog_card)

        # ── 메인 스플리터 ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter { background: transparent; border: none; }")

        # 로그 패널 (좌)
        log_card = QFrame()
        log_card.setStyleSheet(_CARD)
        log_lay = QVBoxLayout(log_card)
        log_lay.setContentsMargins(12, 12, 12, 12)
        log_lay.setSpacing(6)

        log_hdr = QLabel("실행 로그")
        log_hdr.setStyleSheet(
            "QLabel { background: transparent; border: none;"
            " font-size: 15px; font-weight: 700; color: #1e293b;"
            " padding-bottom: 6px; border-bottom: 1px solid #f1f5f9; }"
        )
        log_lay.addWidget(log_hdr)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setStyleSheet(
            "QPlainTextEdit {"
            " background-color: #ffffff; color: #334155;"
            " border: none; border-radius: 4px; padding: 4px;"
            "}"
        )
        log_lay.addWidget(self._log)
        splitter.addWidget(log_card)

        # TC 테이블 패널 (우)
        tc_card = QFrame()
        tc_card.setStyleSheet(_CARD)
        tc_lay = QVBoxLayout(tc_card)
        tc_lay.setContentsMargins(12, 12, 12, 12)
        tc_lay.setSpacing(6)

        tc_hdr_row = QHBoxLayout()
        tc_title = QLabel("TC 목록")
        tc_title.setStyleSheet(
            "QLabel { background: transparent; border: none;"
            " font-size: 15px; font-weight: 700; color: #1e293b; }"
        )
        tc_hdr_row.addWidget(tc_title)
        tc_hdr_row.addStretch()
        self._tc_count_lbl = QLabel("총 0건")
        self._tc_count_lbl.setStyleSheet(
            "QLabel { font-size: 11px; color: #64748b;"
            " background-color: #f8fafc; border: 1px solid #e2e8f0;"
            " border-radius: 4px; padding: 2px 8px; }"
        )
        tc_hdr_row.addWidget(self._tc_count_lbl)
        tc_lay.addLayout(tc_hdr_row)

        self._tc_table = QTableWidget(0, 7)
        self._tc_table.setHorizontalHeaderLabels(
            ["TC ID", "시나리오", "입력값", "예상값", "기법", "상태", "결과"]
        )
        hdr = self._tc_table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        hdr.setDefaultSectionSize(90)
        self._tc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tc_table.setStyleSheet(
            "QTableWidget { border: none; background: #ffffff; }"
            "QHeaderView::section { background-color: #f8fafc; color: #64748b;"
            " font-size: 12px; font-weight: 600; padding: 6px 8px;"
            " border: none; border-bottom: 1px solid #e2e8f0; }"
            "QTableWidget::item { border-bottom: 1px solid #f1f5f9; padding: 4px 8px; }"
        )
        tc_lay.addWidget(self._tc_table)
        splitter.addWidget(tc_card)

        splitter.setSizes([360, 720])
        root.addWidget(splitter, 1)

        # ── 하단 바 ───────────────────────────────────────────────────────────
        bot_card = QFrame()
        bot_card.setStyleSheet(_CARD)
        bot_card.setFixedHeight(52)
        bot_lay = QHBoxLayout(bot_card)
        bot_lay.setContentsMargins(16, 0, 16, 0)
        bot_lay.setSpacing(12)

        # 왼쪽: 상태 인디케이터
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._dot.setStyleSheet(
            "QLabel { border-radius: 4px; border: none; background: #cbd5e1; }"
        )
        self._status_lbl = QLabel("대기 중")
        self._status_lbl.setStyleSheet(
            "QLabel { background: transparent; border: none;"
            " font-size: 13px; font-weight: 600; color: #334155; }"
        )
        bot_lay.addWidget(self._dot)
        bot_lay.addWidget(self._status_lbl)
        bot_lay.addStretch()

        # Stage 5~7 대기/실행 버튼 (Stage 3 완료 후 표시)
        self._exec_btn = QPushButton("Stage 5~7 대기")
        self._exec_btn.setEnabled(False)
        self._exec_btn.setVisible(False)
        self._exec_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #ffffff; color: #3b82f6;"
            " border: 1px solid #3b82f6; border-radius: 6px;"
            " padding: 6px 16px; font-size: 13px; font-weight: 600; }"
            "QPushButton:enabled {"
            " background-color: #3b82f6; color: #ffffff; }"
            "QPushButton:enabled:hover { background-color: #2563eb; }"
        )
        self._exec_btn.clicked.connect(self._start_post_gate)
        bot_lay.addWidget(self._exec_btn)

        # Stage 1~3 실행 버튼 (초기 상태)
        self._run_btn = QPushButton("Stage 1~3 실행")
        self._run_btn.setStyleSheet(
            pill_btn(bg="#1a7a3c", bg_hover="#15803d", bg_pressed="#0f6030",
                     bg_disabled="#86efac", fg_disabled="#ffffff")
        )
        self._run_btn.clicked.connect(self._start_pre_gate)
        bot_lay.addWidget(self._run_btn)

        # 기능목록 Excel 다운로드 버튼 (Stage 0 실행 후 Stage 3 완료 시 표시)
        self._feature_dl_btn = QPushButton("⬇ 기능목록 Excel")
        self._feature_dl_btn.setVisible(False)
        self._feature_dl_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #0f766e; color: #ffffff;"
            " border: none; border-radius: 6px;"
            " padding: 6px 14px; font-size: 12px; font-weight: 600; }"
            "QPushButton:hover { background-color: #0d9488; }"
        )
        self._feature_dl_btn.clicked.connect(self._export_features)
        bot_lay.addWidget(self._feature_dl_btn)

        # Stage 4 Reviewer Gate 버튼 (Stage 3 완료 후 표시)
        self._gate_btn = QPushButton("Stage 4: Reviewer Gate 실행")
        self._gate_btn.setEnabled(False)
        self._gate_btn.setVisible(False)
        self._gate_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #3b82f6; color: #ffffff;"
            " border: 1px solid #3b82f6; border-radius: 6px;"
            " padding: 6px 16px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background-color: #2563eb; }"
            "QPushButton:disabled { background-color: #93c5fd; border-color: #93c5fd; }"
        )
        self._gate_btn.clicked.connect(self._open_gate)
        bot_lay.addWidget(self._gate_btn)

        root.addWidget(bot_card)
        self.setStatusBar(QStatusBar())
        self.statusBar().hide()

    # ── Stage 진행 표시기 ─────────────────────────────────────────────────────
    def _update_circles(self, progress: int, badge: str = "") -> None:
        """progress = 현재 활성 stage 번호(1~7). 1..progress-1=완료, progress=활성, 이후=대기."""
        for i, circle in enumerate(self._circles):
            n = i + 1
            if n < progress:
                circle.setStyleSheet(_CIRCLE_DONE)
            elif n == progress:
                circle.setStyleSheet(_CIRCLE_CURRENT)
            else:
                circle.setStyleSheet(_CIRCLE_FUTURE)
        for i, line in enumerate(self._lines):
            line.setStyleSheet(_LINE_DONE if (i + 1) < progress else _LINE_PENDING)
        if badge:
            self._stage_badge.setText(badge)

    def _set_status(self, text: str, active: bool = False) -> None:
        color = "#22c55e" if active else "#cbd5e1"
        self._dot.setStyleSheet(
            f"QLabel {{ border-radius: 4px; border: none; background: {color}; }}"
        )
        self._status_lbl.setText(text)

    # ── Stage 1~3 (Pre-Gate) ─────────────────────────────────────────────────
    def _start_pre_gate(self) -> None:
        self._run_btn.setEnabled(False)
        self._log.clear()
        self._update_circles(1, "Stage 1~3 실행 중")
        self._set_status("Stage 1~3 실행 중")
        self._append_log("Stage 1~3 시작...")

        self._pre_worker = _PreGateWorker(
            orch=self._orch,
            has_files=bool(self._config.input_files),
        )
        self._pre_worker.stage_done.connect(self._on_pre_stage_done)
        self._pre_worker.finished.connect(self._on_pre_gate_done)
        self._pre_worker.error.connect(self._on_error)
        self._pre_worker.start()

    def _on_pre_stage_done(self, n: int) -> None:
        """stage_done emit: n = 현재 진입한 단계 (1~4)."""
        badges = {1: "Stage 2 실행 중", 2: "Stage 3 실행 중",
                  3: "Stage 3 검증 중", 4: "Stage 4 실행 중"}
        self._update_circles(n, badges.get(n, f"Stage {n} 진행 중"))

    def _on_pre_gate_done(self, tcs: list) -> None:
        self._tcs = tcs
        self._refresh_tc_table()
        # 버튼 전환: 실행 버튼 숨기고 Gate + 5~7대기 표시
        self._run_btn.setVisible(False)
        self._exec_btn.setVisible(True)
        self._exec_btn.setEnabled(False)
        self._gate_btn.setVisible(True)
        self._gate_btn.setEnabled(True)
        # Stage 0 스캔 결과 있으면 기능목록 다운로드 버튼 표시
        feature_draft = self._orch.run_dir / "dom-scan" / "feature-spec-draft.json"
        self._feature_dl_btn.setVisible(feature_draft.exists())
        self._write_meta("stage3_done")
        self._set_status(f"Stage 3 완료  |  TC {len(tcs)}개", active=True)
        self._append_log(f"Stage 3 완료 - TC {len(tcs)}개. Reviewer Gate를 진행하세요.")

    # ── Stage 4 Gate ─────────────────────────────────────────────────────────
    def _open_gate(self) -> None:
        self.gate_review_requested.emit(self._tcs)

    def apply_gate(self, decisions: dict) -> None:
        """ReviewerGate 결정 완료 시 main.py에서 호출."""
        self._tcs = self._orch.apply_gate_decisions(decisions)
        self._refresh_tc_table()
        self._gate_btn.setVisible(False)
        self._exec_btn.setEnabled(True)
        self._exec_btn.setText("Stage 5~7 실행")
        self._update_circles(5, "Stage 5 대기 중")
        self._set_status(f"Stage 4 완료  |  TC {len(self._tcs)}개", active=True)
        self._write_meta("stage4_done")
        self._append_log("Gate 결정 반영 완료. Stage 5~7을 실행하세요.")

    # ── Stage 5~7 (Post-Gate) ─────────────────────────────────────────────────
    def _start_post_gate(self) -> None:
        self._exec_btn.setEnabled(False)
        self._update_circles(5, "Stage 5~7 실행 중")
        self._set_status("Stage 5~7 실행 중")
        self._append_log("Stage 5~7 시작...")

        self._post_worker = _PostGateWorker(orch=self._orch)
        self._post_worker.stage_done.connect(self._on_post_stage_done)
        self._post_worker.finished.connect(self._on_post_gate_done)
        self._post_worker.error.connect(self._on_error)
        self._post_worker.start()

    def _on_post_stage_done(self, n: int) -> None:
        """stage_done emit: n = 방금 완료된 단계(5~7). n+1이 다음 활성."""
        badges = {5: "Stage 6 실행 중", 6: "Stage 7 실행 중", 7: "모든 단계 완료"}
        self._update_circles(n + 1, badges.get(n, ""))

    def _on_post_gate_done(self, out: Path) -> None:
        self._tcs = self._orch.tcs
        self._refresh_tc_table()
        self._write_meta("done")
        self._append_log(f"완료 → {out}")

        passed = sum(1 for tc in self._tcs if tc.get("result") == "pass")
        failed = sum(1 for tc in self._tcs if tc.get("result") == "fail")
        total  = len(self._tcs)
        self._set_status(
            f"완료  |  통과 {passed}  실패 {failed}  /  총 {total}개", active=True
        )
        QMessageBox.information(
            self, "실행 완료",
            f"tc_final.xlsx 생성 완료\n\n"
            f"총 {total}개  PASS {passed}  FAIL {failed}\n\n{out}"
        )

    # ── 기능목록 Excel 다운로드 ───────────────────────────────────────────────
    def _export_features(self) -> None:
        """Stage 0 기능 목록(feature-spec-draft.json)을 Excel로 저장."""
        draft_path = self._orch.run_dir / "dom-scan" / "feature-spec-draft.json"
        if not draft_path.exists():
            QMessageBox.warning(self, "알림", "Stage 0 DOM 스캔 결과가 없습니다.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "기능 목록 저장",
            f"feature_list_{self._config.run_id}.xlsx",
            "Excel 파일 (*.xlsx);;모든 파일 (*.*)",
        )
        if not save_path:
            return

        try:
            import json
            from app.tools.excel_builder import build_features
            draft    = json.loads(draft_path.read_text(encoding="utf-8"))
            features = draft.get("features", [])
            if not features:
                QMessageBox.information(self, "알림", "추출된 기능이 없습니다 (features: 0개).")
                return
            build_features(features, save_path)
            QMessageBox.information(
                self, "저장 완료",
                f"기능 목록 {len(features)}개를 저장했습니다:\n{save_path}\n\n"
                f"스크린샷 파일은:\n{self._orch.run_dir / 'dom-scan' / 'screenshots'}",
            )
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", str(e))

    # ── 오류 처리 ─────────────────────────────────────────────────────────────
    def _on_error(self, msg: str) -> None:
        # 어느 단계에서 실패했든 실행 버튼 복원
        self._run_btn.setEnabled(True)
        if not self._run_btn.isVisible():
            self._exec_btn.setEnabled(True)
        self._set_status("오류 발생")
        self._append_log(f"[오류]\n{msg}")
        QMessageBox.critical(self, "오류", msg[:800])

    # ── UI 갱신 ───────────────────────────────────────────────────────────────
    def _append_log(self, msg: str) -> None:
        ts   = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self._log.appendPlainText(line)
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _refresh_tc_table(self) -> None:
        self._tc_table.setRowCount(0)
        self._tc_count_lbl.setText(f"총 {len(self._tcs)}건")

        status_colors = {
            "approved": QColor("#d1fae5"),
            "edited":   QColor("#dbeafe"),
            "rejected": QColor("#fee2e2"),
            "pending":  QColor("#f1f5f9"),
        }
        result_colors = {
            "pass":         QColor("#d1fae5"),
            "fail":         QColor("#fee2e2"),
            "blocked":      QColor("#ffe4e6"),
            "not_executed": QColor("#e2e8f0"),
        }

        for tc in self._tcs:
            r = self._tc_table.rowCount()
            self._tc_table.insertRow(r)

            technique_en = tc.get("design_technique", "")
            status       = tc.get("review_status", "pending")
            result       = tc.get("result", "not_executed")

            bg     = status_colors.get(status, QColor("white"))
            res_bg = result_colors.get(result, QColor("white"))

            cells = [
                (0, tc.get("tc_id", ""),             bg),
                (1, tc.get("scenario", ""),           bg),
                (2, tc.get("precondition", "")[:80],  bg),
                (3, tc.get("expected", "")[:80],      bg),
                (4, _TECHNIQUE_KO.get(technique_en, technique_en), bg),
                (5, _STATUS_KO.get(status, status),   bg),
                (6, _RESULT_KO.get(result, result),   res_bg),
            ]
            for col, text, color in cells:
                item = QTableWidgetItem(text)
                item.setBackground(color)
                self._tc_table.setItem(r, col, item)

    # ── 메타 저장 ─────────────────────────────────────────────────────────────
    def _write_meta(self, stage: str) -> None:
        try:
            meta = {
                "run_id":     self._config.run_id,
                "target_url": self._config.target_url,
                "stage":      stage,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            (self._orch.run_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass
