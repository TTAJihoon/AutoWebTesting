"""Stage 4 Reviewer Gate — TC별 A/E/R/P 결정 UI (D45: PySide6)."""
from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QTextEdit, QSplitter, QWidget, QMessageBox, QStatusBar,
    QMainWindow,
)

_STATUS_OPTIONS = ["pending", "approved", "edited", "rejected"]
_STATUS_COLORS = {
    "approved": QColor("#d1fae5"),
    "edited": QColor("#dbeafe"),
    "rejected": QColor("#fee2e2"),
    "pending": QColor("#fef9c3"),
}


class ReviewerGate(QDialog):
    """TC 목록에 대해 A/E/R/P 결정. decisions_ready(dict) 시그널로 결과 전달."""

    decisions_ready = Signal(dict)  # {tc_id: {status, note}}

    def __init__(self, tcs: list[dict], reviewer_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stage 4 — Reviewer Gate")
        self.resize(1100, 680)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._tcs = tcs
        self._reviewer_id = reviewer_id
        self._decisions: dict[str, dict] = {
            tc["tc_id"]: {
                "status": tc.get("review_status", "pending"),
                "note": tc.get("reviewer_note", ""),
                "reviewer_id": reviewer_id,
            }
            for tc in tcs
        }
        self._build_ui()
        self._load_tcs()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # 요약 바
        summary_row = QHBoxLayout()
        self._summary_lbl = QLabel()
        summary_row.addWidget(self._summary_lbl)
        summary_row.addStretch()

        # 일괄 처리 버튼
        approve_all = QPushButton("전체 승인")
        approve_all.clicked.connect(lambda: self._set_all("approved"))
        reject_all = QPushButton("전체 거부")
        reject_all.clicked.connect(lambda: self._set_all("rejected"))
        summary_row.addWidget(approve_all)
        summary_row.addWidget(reject_all)
        root.addLayout(summary_row)

        # 스플리터: 테이블 | 상세
        splitter = QSplitter(Qt.Horizontal)

        # TC 테이블
        tc_panel = QWidget()
        tc_lay = QVBoxLayout(tc_panel)
        tc_lay.setContentsMargins(0, 0, 0, 0)
        tc_lay.addWidget(QLabel("<b>TC 목록</b>"))
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["TC ID", "대분류", "시나리오", "기법", "상태"])
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.currentRowChanged.connect(self._on_row_changed)
        tc_lay.addWidget(self._table)
        splitter.addWidget(tc_panel)

        # 상세 패널
        detail_panel = QWidget()
        detail_lay = QVBoxLayout(detail_panel)
        detail_lay.setContentsMargins(8, 0, 0, 0)
        detail_lay.setSpacing(10)
        detail_lay.addWidget(QLabel("<b>TC 상세</b>"))

        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setFont(QFont("Consolas", 9))
        detail_lay.addWidget(self._detail_text)

        detail_lay.addWidget(QLabel("결정"))
        self._status_combo = QComboBox()
        self._status_combo.addItems(_STATUS_OPTIONS)
        self._status_combo.currentTextChanged.connect(self._on_status_changed)
        detail_lay.addWidget(self._status_combo)

        detail_lay.addWidget(QLabel("검토 노트"))
        self._note_edit = QTextEdit()
        self._note_edit.setFixedHeight(80)
        self._note_edit.textChanged.connect(self._on_note_changed)
        detail_lay.addWidget(self._note_edit)

        apply_btn = QPushButton("이 TC에 적용")
        apply_btn.clicked.connect(self._apply_current)
        detail_lay.addWidget(apply_btn)
        detail_lay.addStretch()
        splitter.addWidget(detail_panel)

        splitter.setSizes([650, 430])
        root.addWidget(splitter)

        # 하단 버튼
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        self._submit_btn = QPushButton("결정 완료 → Stage 5 진행")
        self._submit_btn.setStyleSheet(
            "QPushButton{background:#7c3aed;color:white;border-radius:4px;padding:4px 16px;}"
            "QPushButton:hover{background:#6d28d9;}"
        )
        self._submit_btn.clicked.connect(self._submit)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._submit_btn)
        root.addLayout(btn_row)

    # ── 데이터 로딩 ──────────────────────────────────────────────────────
    def _load_tcs(self) -> None:
        self._table.setRowCount(0)
        for tc in self._tcs:
            r = self._table.rowCount()
            self._table.insertRow(r)
            status = self._decisions[tc["tc_id"]]["status"]
            items = [
                QTableWidgetItem(tc.get("tc_id", "")),
                QTableWidgetItem(tc.get("대분류", "")),
                QTableWidgetItem(tc.get("scenario", "")[:60]),
                QTableWidgetItem(tc.get("design_technique", "")),
                QTableWidgetItem(status),
            ]
            bg = _STATUS_COLORS.get(status, QColor("white"))
            for item in items:
                item.setBackground(bg)
            for col, item in enumerate(items):
                self._table.setItem(r, col, item)
        self._update_summary()

    def _on_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._tcs):
            return
        tc = self._tcs[row]
        tc_id = tc["tc_id"]
        dec = self._decisions[tc_id]

        detail_lines = [
            f"TC ID: {tc.get('tc_id')}",
            f"대분류: {tc.get('대분류', '')} / {tc.get('중분류', '')} / {tc.get('소분류', '')}",
            f"시나리오: {tc.get('scenario', '')}",
            f"사전조건: {tc.get('precondition', '')}",
            f"기대출력: {tc.get('expected', '')}",
            f"설계기법: {tc.get('design_technique', '')}",
            f"요구사항 ID: {tc.get('requirement_id', '')}",
            f"source_quote: {tc.get('source_quote', '')[:120]}",
            f"gen_confidence: {tc.get('gen_confidence', '')}",
        ]
        self._detail_text.setPlainText("\n\n".join(detail_lines))

        self._status_combo.blockSignals(True)
        self._status_combo.setCurrentText(dec["status"])
        self._status_combo.blockSignals(False)

        self._note_edit.blockSignals(True)
        self._note_edit.setPlainText(dec.get("note", ""))
        self._note_edit.blockSignals(False)

    def _on_status_changed(self, value: str) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        tc_id = self._tcs[row]["tc_id"]
        self._decisions[tc_id]["status"] = value

    def _on_note_changed(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        tc_id = self._tcs[row]["tc_id"]
        self._decisions[tc_id]["note"] = self._note_edit.toPlainText()

    def _apply_current(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        tc = self._tcs[row]
        tc_id = tc["tc_id"]
        dec = self._decisions[tc_id]
        status = dec["status"]
        bg = _STATUS_COLORS.get(status, QColor("white"))
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(bg)
        self._table.item(row, 4).setText(status)
        self._update_summary()

    def _set_all(self, status: str) -> None:
        for tc_id in self._decisions:
            self._decisions[tc_id]["status"] = status
        for r in range(self._table.rowCount()):
            bg = _STATUS_COLORS.get(status, QColor("white"))
            for c in range(self._table.columnCount()):
                item = self._table.item(r, c)
                if item:
                    item.setBackground(bg)
            self._table.item(r, 4).setText(status)
        self._update_summary()

    def _update_summary(self) -> None:
        counts: dict[str, int] = {"approved": 0, "edited": 0, "rejected": 0, "pending": 0}
        for d in self._decisions.values():
            counts[d["status"]] = counts.get(d["status"], 0) + 1
        self._summary_lbl.setText(
            f"총 {len(self._tcs)}개  |  "
            f"승인 {counts['approved']}  편집 {counts['edited']}  "
            f"거부 {counts['rejected']}  보류 {counts['pending']}"
        )

    def _submit(self) -> None:
        pending = sum(1 for d in self._decisions.values() if d["status"] == "pending")
        if pending > 0:
            res = QMessageBox.question(
                self, "확인",
                f"{pending}개 TC가 아직 '보류' 상태입니다. 그대로 완료하시겠습니까?\n"
                "(보류 TC는 Stage 5 자동 실행에서 제외됩니다.)",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.No:
                return
        self.decisions_ready.emit(self._decisions)
        self.accept()
