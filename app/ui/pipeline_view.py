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
            if not self._has_files:
                self._orch.run_stage0()
                self.stage_done.emit(1)
            self._orch.run_stage1()
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
            "QPushButton{background:#16a34a;color:white;border-radius:4px;padding:4px 14px;}"
            "QPushButton:hover{background:#15803d;}"
            "QPushButton:disabled{background:#86efac;}"
        )
        self._run_btn.clicked.connect(self._start_pre_gate)
        info_row.addWidget(self._run_btn)
        root.addLayout(info_row)

        # 진행 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 7)
        self._progress_bar.setValue(0)
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

        self._exec_btn = QPushButton("Stage 5~7 실행")
        self._exec_btn.setEnabled(False)
        self._exec_btn.setStyleSheet(
            "QPushButton{background:#2563eb;color:white;border-radius:4px;padding:4px 14px;}"
            "QPushButton:hover{background:#1d4ed8;}"
            "QPushButton:disabled{background:#93c5fd;}"
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
        self._append_log(f"[{datetime.now():%H:%M:%S}] Stage 1~3 시작...")

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
        self._write_meta("stage3_done")
        self._append_log(f"[{datetime.now():%H:%M:%S}] Stage 3 완료 — TC {len(tcs)}개. Reviewer Gate를 진행하세요.")
        self.statusBar().showMessage(f"Stage 3 완료 — TC {len(tcs)}개")

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
        self._append_log(f"[{datetime.now():%H:%M:%S}] Gate 결정 반영 완료. Stage 5~7을 실행하세요.")

    # ── Stage 5~7 (Post-Gate) ─────────────────────────────────────────────
    def _start_post_gate(self) -> None:
        self._exec_btn.setEnabled(False)
        self._append_log(f"[{datetime.now():%H:%M:%S}] Stage 5~7 시작...")

        self._post_worker = _PostGateWorker(orch=self._orch)
        self._post_worker.stage_done.connect(self._progress_bar.setValue)
        self._post_worker.finished.connect(self._on_post_gate_done)
        self._post_worker.error.connect(self._on_error)
        self._post_worker.start()

    def _on_post_gate_done(self, out: Path) -> None:
        self._tcs = self._orch.tcs
        self._refresh_tc_table()
        self._write_meta("done")
        self._append_log(f"[{datetime.now():%H:%M:%S}] 완료 -> {out}")
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
        self._append_log(f"[오류]\n{msg}")
        self.statusBar().showMessage("오류 발생")
        QMessageBox.critical(self, "오류", msg[:800])

    # ── UI 갱신 ──────────────────────────────────────────────────────────
    def _append_log(self, msg: str) -> None:
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
