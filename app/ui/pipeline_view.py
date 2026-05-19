"""파이프라인 실행 진행 창 — Stage 0~7 실시간 로그 (D45: PySide6)."""
from __future__ import annotations
import json
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


class _PipelineWorker(QThread):
    """백그라운드에서 Stage 1~3 + 5~7 실행."""

    progress = Signal(str)
    stage_done = Signal(int, object)   # stage_num, result
    finished = Signal(Path)
    error = Signal(str)

    def __init__(
        self,
        orch: Orchestrator,
        skip_stage0: bool,
        gate_decisions: dict,
    ):
        super().__init__()
        self._orch = orch
        self._skip_stage0 = skip_stage0
        self._gate = gate_decisions

    def run(self) -> None:
        try:
            out = self._orch.run_pipeline(
                skip_stage0=self._skip_stage0,
                gate_decisions=self._gate,
            )
            self.finished.emit(out)
        except Exception as e:
            self.error.emit(str(e))


class PipelineView(QMainWindow):
    """파이프라인 실행 창. gate_decisions 주입으로 Stage 4 반영."""

    gate_review_requested = Signal(list)   # tcs → reviewer_gate 열기

    def __init__(self, config: RunConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"AWT 실행 — {config.run_id}")
        self.resize(1000, 660)
        self._config = config
        self._orch = Orchestrator(config, progress_cb=self._on_progress)
        self._worker: _PipelineWorker | None = None
        self._tcs: list[dict] = []
        self._gate_decisions: dict = {}
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        # 상단 정보
        info_row = QHBoxLayout()
        self._url_lbl = QLabel(f"대상: {self._config.target_url}")
        self._url_lbl.setStyleSheet("font-weight:bold;")
        info_row.addWidget(self._url_lbl)
        info_row.addStretch()
        self._run_btn = QPushButton("▶ Stage 1~3 실행")
        self._run_btn.setStyleSheet(
            "QPushButton{background:#16a34a;color:white;border-radius:4px;padding:4px 14px;}"
            "QPushButton:hover{background:#15803d;}"
            "QPushButton:disabled{background:#86efac;}"
        )
        self._run_btn.clicked.connect(self._start_pipeline)
        info_row.addWidget(self._run_btn)
        root.addLayout(info_row)

        # 진행 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 7)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("Stage %v / 7")
        root.addWidget(self._progress_bar)

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
        self._tc_table = QTableWidget(0, 5)
        self._tc_table.setHorizontalHeaderLabels(["TC ID", "시나리오", "기법", "상태", "결과"])
        self._tc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._tc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        tc_lay.addWidget(self._tc_table)

        self._gate_btn = QPushButton("Stage 4: Reviewer Gate →")
        self._gate_btn.setEnabled(False)
        self._gate_btn.setStyleSheet(
            "QPushButton{background:#7c3aed;color:white;border-radius:4px;padding:4px 14px;}"
            "QPushButton:hover{background:#6d28d9;}"
            "QPushButton:disabled{background:#c4b5fd;}"
        )
        self._gate_btn.clicked.connect(self._open_gate)
        tc_lay.addWidget(self._gate_btn)

        self._exec_btn = QPushButton("▶ Stage 5~7 실행")
        self._exec_btn.setEnabled(False)
        self._exec_btn.setStyleSheet(
            "QPushButton{background:#2563eb;color:white;border-radius:4px;padding:4px 14px;}"
            "QPushButton:hover{background:#1d4ed8;}"
            "QPushButton:disabled{background:#93c5fd;}"
        )
        self._exec_btn.clicked.connect(self._start_exec)
        tc_lay.addWidget(self._exec_btn)
        splitter.addWidget(tc_widget)

        splitter.setSizes([380, 600])
        root.addWidget(splitter)

        self.setStatusBar(QStatusBar())

    # ── 파이프라인 제어 ───────────────────────────────────────────────────
    def _start_pipeline(self) -> None:
        self._run_btn.setEnabled(False)
        self._log.clear()
        self._progress_bar.setValue(0)

        try:
            if not self._config.input_files:
                self._orch.run_stage0()
                self._progress_bar.setValue(1)
            self._orch.run_stage1()
            self._progress_bar.setValue(2)
            self._orch.run_stage2()
            self._progress_bar.setValue(3)
            self._tcs = self._orch.run_stage3()
            self._progress_bar.setValue(4)
            self._refresh_tc_table()
            self._gate_btn.setEnabled(True)
            self._on_progress("▶ Stage 3 완료. Reviewer Gate를 진행하세요.")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
            self._run_btn.setEnabled(True)

    def _open_gate(self) -> None:
        self.gate_review_requested.emit(self._tcs)

    def apply_gate(self, decisions: dict) -> None:
        """ReviewerGate에서 결정이 완료되면 호출됨."""
        self._gate_decisions = decisions
        self._tcs = self._orch.apply_gate_decisions(decisions)
        self._refresh_tc_table()
        self._exec_btn.setEnabled(True)
        self._gate_btn.setEnabled(False)
        self._on_progress("▶ Gate 결정 반영 완료. Stage 5~7을 실행하세요.")

    def _start_exec(self) -> None:
        self._exec_btn.setEnabled(False)
        try:
            self._tcs = self._orch.run_stage5()
            self._progress_bar.setValue(5)
            self._tcs = self._orch.run_stage6()
            self._progress_bar.setValue(6)
            out = self._orch.run_stage7()
            self._progress_bar.setValue(7)
            self._refresh_tc_table()
            self._on_progress(f"✅ 완료 → {out}")
            QMessageBox.information(self, "완료", f"tc_final.xlsx 생성:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    # ── UI 갱신 ──────────────────────────────────────────────────────────
    def _on_progress(self, msg: str) -> None:
        self._log.appendPlainText(msg)
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
            items = [
                QTableWidgetItem(tc.get("tc_id", "")),
                QTableWidgetItem(tc.get("scenario", "")[:60]),
                QTableWidgetItem(tc.get("design_technique", "")),
                QTableWidgetItem(tc.get("review_status", "pending")),
                QTableWidgetItem(tc.get("result", "not_executed")),
            ]
            bg = status_colors.get(tc.get("review_status", ""), QColor("white"))
            for item in items:
                item.setBackground(bg)
            self._tc_table.setItem(r, 0, items[0])
            self._tc_table.setItem(r, 1, items[1])
            self._tc_table.setItem(r, 2, items[2])
            self._tc_table.setItem(r, 3, items[3])
            res_item = items[4]
            res_item.setBackground(result_colors.get(tc.get("result", ""), QColor("white")))
            self._tc_table.setItem(r, 4, res_item)
