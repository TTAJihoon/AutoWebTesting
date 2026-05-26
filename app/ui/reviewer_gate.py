"""Stage 4 Reviewer Gate — TC별 A/E/R/P 결정 UI (D45: PySide6)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QTextEdit, QSplitter, QWidget, QMessageBox, QFileDialog,
    QFrame,
)

_STATUS_OPTIONS = ["pending", "approved", "edited", "rejected"]
_STATUS_KO = {
    "pending":  "검토 전",
    "approved": "승인",
    "edited":   "수정",
    "rejected": "거부",
}
_STATUS_COLORS = {
    "approved": QColor("#d1fae5"),
    "edited":   QColor("#dbeafe"),
    "rejected": QColor("#fee2e2"),
    "pending":  QColor("#fef9c3"),
}

# 상세 팝업에 표시할 TC 필드
_TC_FIELDS: list[tuple[str, str]] = [
    ("tc_id",            "TC ID"),
    ("대분류",            "대분류"),
    ("중분류",            "중분류"),
    ("소분류",            "소분류"),
    ("scenario",         "시나리오"),
    ("precondition",     "사전조건"),
    ("expected",         "기대출력"),
    ("design_technique", "설계기법"),
    ("requirement_id",   "요구사항 ID"),
    ("source_quote",     "근거 문구"),
    ("gen_confidence",   "생성 신뢰도"),
]

_CARD = (
    "QFrame { background-color: #ffffff; border-radius: 8px;"
    " border: 1px solid #e2e8f0; }"
)
_SUBHDR = (
    "QFrame { background-color: #f8fafc;"
    " border-top-left-radius: 8px; border-top-right-radius: 8px;"
    " border-bottom: 1px solid #e2e8f0; border-left: none;"
    " border-right: none; border-top: none; }"
)


# ── TC 상세 팝업 ────────────────────────────────────────────────────────────
class _TcDetailDialog(QDialog):
    """더블클릭 시 표시되는 TC 전체 내용 팝업."""

    def __init__(self, tc: dict, parent=None):
        super().__init__(parent)
        tc_id = tc.get("tc_id", "?")
        self.setWindowTitle(f"TC 상세 — {tc_id}")
        self.resize(680, 540)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet("QDialog { background-color: #f1f5f9; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # 제목
        hdr_lbl = QLabel(
            f"<span style='font-size:15px; font-weight:700; color:#1e293b;'>{tc_id}</span>"
        )
        root.addWidget(hdr_lbl)

        # 내용 카드
        card = QFrame()
        card.setStyleSheet(_CARD)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)

        # 서브헤더
        sub = QFrame()
        sub.setFixedHeight(36)
        sub.setStyleSheet(_SUBHDR)
        sub_lay = QHBoxLayout(sub)
        sub_lay.setContentsMargins(14, 0, 14, 0)
        sub_lay.addWidget(QLabel("<b style='color:#64748b; font-size:12px;'>전체 내용</b>"))
        card_lay.addWidget(sub)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setFont(QFont("Segoe UI", 10))
        txt.setStyleSheet(
            "QTextEdit { background-color: #ffffff; border: none;"
            " color: #1e293b; padding: 12px; }"
        )

        # HTML 렌더링으로 줄바꿈 포함 전체 내용 표시
        html_parts: list[str] = []
        for key, label in _TC_FIELDS:
            val = tc.get(key, "")
            if val is None:
                val = ""
            val = str(val)
            if val.strip():
                escaped = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_parts.append(
                    f"<p style='margin:0 0 2px 0;'>"
                    f"<span style='color:#64748b; font-size:11px; font-weight:600;'>{label}</span>"
                    f"</p>"
                    f"<p style='margin:0 0 12px 0; color:#1e293b;'>{escaped}</p>"
                )
        txt.setHtml("".join(html_parts))
        card_lay.addWidget(txt)
        root.addWidget(card)

        close_btn = QPushButton("닫기")
        close_btn.setFixedHeight(36)
        close_btn.setStyleSheet(
            "QPushButton { background: #3b82f6; color: #ffffff; border-radius: 6px;"
            " font-size: 13px; font-weight: 600; border: none; padding: 0 20px; }"
            "QPushButton:hover { background: #2563eb; }"
        )
        close_btn.clicked.connect(self.accept)
        root.addWidget(close_btn, alignment=Qt.AlignRight)


# ── Reviewer Gate 메인 다이얼로그 ────────────────────────────────────────────
class ReviewerGate(QDialog):
    """TC 목록에 대해 A/E/R/P 결정. decisions_ready(dict) 시그널로 결과 전달."""

    decisions_ready = Signal(dict)  # {tc_id: {status, note}}

    def __init__(self, tcs: list[dict], reviewer_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stage 4 — Reviewer Gate")
        self.resize(1200, 720)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet("QDialog { background-color: #f1f5f9; }")

        self._tcs = tcs
        self._reviewer_id = reviewer_id
        self._decisions: dict[str, dict] = {
            tc.get("tc_id", f"__unknown_{i}__"): {
                "status": tc.get("review_status", "pending"),
                "note":   tc.get("reviewer_note", ""),
                "reviewer_id": reviewer_id,
            }
            for i, tc in enumerate(tcs)
        }
        self._build_ui()
        self._load_tcs()

    # ── UI 구성 ──────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # ── 상단 요약 바 ──────────────────────────────────────────────────
        top_card = QFrame()
        top_card.setStyleSheet(_CARD)
        top_lay = QHBoxLayout(top_card)
        top_lay.setContentsMargins(16, 10, 16, 10)
        top_lay.setSpacing(10)

        top_lay.addWidget(
            QLabel("<b style='font-size:15px; color:#1e293b;'>Stage 4 — Reviewer Gate</b>")
        )

        self._summary_lbl = QLabel()
        self._summary_lbl.setStyleSheet("color: #64748b; font-size: 13px;")
        top_lay.addWidget(self._summary_lbl)
        top_lay.addStretch()

        # 일괄 처리 버튼
        approve_all = QPushButton("전체 승인")
        approve_all.setFixedHeight(32)
        approve_all.setStyleSheet(
            "QPushButton { background: #16a34a; color: #ffffff; border-radius: 6px;"
            " padding: 0 14px; font-size: 12px; font-weight: 600; border: none; }"
            "QPushButton:hover { background: #15803d; }"
        )
        approve_all.clicked.connect(lambda: self._set_all("approved"))
        top_lay.addWidget(approve_all)

        reject_all = QPushButton("전체 거부")
        reject_all.setFixedHeight(32)
        reject_all.setStyleSheet(
            "QPushButton { background: #dc2626; color: #ffffff; border-radius: 6px;"
            " padding: 0 14px; font-size: 12px; font-weight: 600; border: none; }"
            "QPushButton:hover { background: #b91c1c; }"
        )
        reject_all.clicked.connect(lambda: self._set_all("rejected"))
        top_lay.addWidget(reject_all)

        # Excel 다운로드 버튼
        excel_btn = QPushButton("⬇ Excel 다운로드")
        excel_btn.setFixedHeight(32)
        excel_btn.setStyleSheet(
            "QPushButton { background: #0f766e; color: #ffffff; border-radius: 6px;"
            " padding: 0 14px; font-size: 12px; font-weight: 600; border: none; }"
            "QPushButton:hover { background: #0d9488; }"
        )
        excel_btn.clicked.connect(self._export_excel)
        top_lay.addWidget(excel_btn)

        root.addWidget(top_card)

        # ── 스플리터: TC 테이블 | 상세 패널 ─────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # ── 왼쪽: TC 테이블 카드 ──────────────────────────────────────────
        table_card = QFrame()
        table_card.setStyleSheet(_CARD)
        table_card_lay = QVBoxLayout(table_card)
        table_card_lay.setContentsMargins(0, 0, 0, 0)
        table_card_lay.setSpacing(0)

        # 테이블 헤더 행
        t_hdr = QFrame()
        t_hdr.setFixedHeight(36)
        t_hdr.setStyleSheet(_SUBHDR)
        t_hdr_lay = QHBoxLayout(t_hdr)
        t_hdr_lay.setContentsMargins(14, 0, 14, 0)
        t_hdr_lay.addWidget(QLabel("<b style='color:#1e293b;'>TC 목록</b>"))
        t_hdr_lay.addWidget(
            QLabel("<span style='color:#94a3b8; font-size:11px;'>더블클릭 → 전체 내용</span>")
        )
        t_hdr_lay.addStretch()
        table_card_lay.addWidget(t_hdr)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["TC ID", "대분류", "시나리오", "기법", "상태"])

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)   # 드래그로 너비 조절 가능
        hh.setStretchLastSection(False)
        # 초기 컬럼 너비
        self._table.setColumnWidth(0, 100)   # TC ID
        self._table.setColumnWidth(1, 110)   # 대분류
        self._table.setColumnWidth(2, 360)   # 시나리오 (가장 넓게)
        self._table.setColumnWidth(3, 130)   # 기법
        self._table.setColumnWidth(4, 75)    # 상태

        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.setStyleSheet(
            "QTableWidget { border: none; background-color: #ffffff;"
            " gridline-color: #f1f5f9; outline: none; }"
            "QHeaderView::section { background-color: #f8fafc; color: #64748b;"
            " font-weight: 600; font-size: 12px; border: none;"
            " border-bottom: 1px solid #e2e8f0; padding: 6px 8px; }"
            "QTableWidget::item { padding: 4px 8px; color: #1e293b; }"
            "QTableWidget::item:selected { background-color: #eff6ff; color: #1e293b; }"
        )

        # ← 핵심 수정: currentRowChanged 대신 currentCellChanged 사용
        self._table.currentCellChanged.connect(
            lambda cur_row, _cur_col, _prev_row, _prev_col:
                self._on_row_changed(cur_row)
        )
        # 더블클릭 → 전체 내용 팝업
        self._table.cellDoubleClicked.connect(self._on_double_click)

        table_card_lay.addWidget(self._table)
        splitter.addWidget(table_card)

        # ── 오른쪽: 상세 / 결정 카드 ────────────────────────────────────
        detail_card = QFrame()
        detail_card.setStyleSheet(_CARD)
        detail_card_lay = QVBoxLayout(detail_card)
        detail_card_lay.setContentsMargins(0, 0, 0, 0)
        detail_card_lay.setSpacing(0)

        d_hdr = QFrame()
        d_hdr.setFixedHeight(36)
        d_hdr.setStyleSheet(_SUBHDR)
        d_hdr_lay = QHBoxLayout(d_hdr)
        d_hdr_lay.setContentsMargins(14, 0, 14, 0)
        d_hdr_lay.addWidget(QLabel("<b style='color:#1e293b;'>TC 상세 / 결정</b>"))
        detail_card_lay.addWidget(d_hdr)

        # 상세 본문 영역
        detail_body = QWidget()
        detail_body.setStyleSheet("QWidget { background: transparent; border: none; }")
        body_lay = QVBoxLayout(detail_body)
        body_lay.setContentsMargins(14, 12, 14, 14)
        body_lay.setSpacing(8)

        # 요약 텍스트 (선택 행 정보)
        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setFont(QFont("Segoe UI", 10))
        self._detail_text.setStyleSheet(
            "QTextEdit { background-color: #f8fafc; border: 1px solid #e2e8f0;"
            " border-radius: 6px; color: #1e293b; padding: 8px; }"
        )
        body_lay.addWidget(self._detail_text, stretch=3)

        # 결정 콤보
        body_lay.addWidget(
            QLabel("<span style='color:#64748b; font-size:11px; font-weight:600;'>결정</span>")
        )
        self._status_combo = QComboBox()
        self._status_combo.addItems([_STATUS_KO[s] for s in _STATUS_OPTIONS])
        self._status_combo.setFixedHeight(34)
        self._status_combo.setStyleSheet(
            "QComboBox { border: 1px solid #e2e8f0; border-radius: 6px;"
            " background: #ffffff; padding: 4px 10px; color: #1e293b; font-size: 13px; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            "QComboBox QAbstractItemView { border: 1px solid #e2e8f0; background: #ffffff; }"
        )
        self._status_combo.currentIndexChanged.connect(self._on_status_changed)
        body_lay.addWidget(self._status_combo)

        # 검토 노트
        body_lay.addWidget(
            QLabel("<span style='color:#64748b; font-size:11px; font-weight:600;'>검토 노트</span>")
        )
        self._note_edit = QTextEdit()
        self._note_edit.setFixedHeight(80)
        self._note_edit.setStyleSheet(
            "QTextEdit { border: 1px solid #e2e8f0; border-radius: 6px;"
            " background: #ffffff; color: #1e293b; padding: 4px 8px; font-size: 13px; }"
        )
        self._note_edit.textChanged.connect(self._on_note_changed)
        body_lay.addWidget(self._note_edit)

        apply_btn = QPushButton("이 TC에 적용")
        apply_btn.setFixedHeight(36)
        apply_btn.setStyleSheet(
            "QPushButton { background: #3b82f6; color: #ffffff; border-radius: 6px;"
            " font-size: 13px; font-weight: 600; border: none; }"
            "QPushButton:hover { background: #2563eb; }"
        )
        apply_btn.clicked.connect(self._apply_current)
        body_lay.addWidget(apply_btn)
        body_lay.addStretch()

        detail_card_lay.addWidget(detail_body, stretch=1)
        splitter.addWidget(detail_card)

        splitter.setSizes([760, 420])
        root.addWidget(splitter, stretch=1)

        # ── 하단 버튼 바 ──────────────────────────────────────────────────
        bot_card = QFrame()
        bot_card.setStyleSheet(_CARD)
        bot_lay = QHBoxLayout(bot_card)
        bot_lay.setContentsMargins(16, 10, 16, 10)

        cancel_btn = QPushButton("취소")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet(
            "QPushButton { background: #ffffff; color: #64748b;"
            " border: 1px solid #e2e8f0; border-radius: 6px;"
            " font-size: 13px; padding: 0 18px; }"
            "QPushButton:hover { background: #f8fafc; }"
        )
        cancel_btn.clicked.connect(self.reject)

        self._submit_btn = QPushButton("결정 완료 → Stage 5 진행")
        self._submit_btn.setFixedHeight(36)
        self._submit_btn.setStyleSheet(
            "QPushButton { background: #7c3aed; color: #ffffff; border-radius: 6px;"
            " font-size: 13px; font-weight: 600; border: none; padding: 0 20px; }"
            "QPushButton:hover { background: #6d28d9; }"
        )
        self._submit_btn.clicked.connect(self._submit)

        bot_lay.addWidget(cancel_btn)
        bot_lay.addStretch()
        bot_lay.addWidget(self._submit_btn)
        root.addWidget(bot_card)

    # ── 데이터 로딩 ──────────────────────────────────────────────────────
    def _load_tcs(self) -> None:
        self._table.setRowCount(0)
        for i, tc in enumerate(self._tcs):
            r = self._table.rowCount()
            self._table.insertRow(r)
            tc_id = tc.get("tc_id", f"__unknown_{i}__")
            status = self._decisions.get(tc_id, {}).get("status", "pending")
            items = [
                QTableWidgetItem(tc_id),
                QTableWidgetItem(tc.get("대분류", "")),
                QTableWidgetItem(tc.get("scenario", "")),     # 잘림 없이 전체 저장
                QTableWidgetItem(tc.get("design_technique", "")),
                QTableWidgetItem(_STATUS_KO.get(status, status)),
            ]
            bg = _STATUS_COLORS.get(status, QColor("#ffffff"))
            for item in items:
                item.setBackground(bg)
            for col, item in enumerate(items):
                self._table.setItem(r, col, item)
        self._update_summary()

    # ── 이벤트 핸들러 ────────────────────────────────────────────────────
    def _on_row_changed(self, row: int) -> None:
        """테이블 선택 행 변경 시 상세 패널 갱신."""
        if row < 0 or row >= len(self._tcs):
            return
        tc = self._tcs[row]
        tc_id = tc.get("tc_id", f"__unknown_{row}__")
        dec = self._decisions.get(tc_id, {"status": "pending", "note": ""})

        lines = []
        for key, label in _TC_FIELDS:
            val = tc.get(key, "")
            if val:
                lines.append(f"[{label}]\n{val}")
        self._detail_text.setPlainText("\n\n".join(lines))

        # 콤보 인덱스 설정 (blockSignals로 _on_status_changed 억제)
        status = dec.get("status", "pending")
        idx = _STATUS_OPTIONS.index(status) if status in _STATUS_OPTIONS else 0
        self._status_combo.blockSignals(True)
        self._status_combo.setCurrentIndex(idx)
        self._status_combo.blockSignals(False)

        self._note_edit.blockSignals(True)
        self._note_edit.setPlainText(dec.get("note", ""))
        self._note_edit.blockSignals(False)

    def _on_double_click(self, row: int, _col: int) -> None:
        """더블클릭 → TC 전체 내용 팝업."""
        if row < 0 or row >= len(self._tcs):
            return
        dlg = _TcDetailDialog(self._tcs[row], parent=self)
        dlg.exec()

    def _on_status_changed(self, index: int) -> None:
        row = self._table.currentRow()
        if row < 0 or index < 0 or index >= len(_STATUS_OPTIONS):
            return
        tc_id = self._tcs[row].get("tc_id", f"__unknown_{row}__")
        if tc_id in self._decisions:
            self._decisions[tc_id]["status"] = _STATUS_OPTIONS[index]

    def _on_note_changed(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        tc_id = self._tcs[row].get("tc_id", f"__unknown_{row}__")
        if tc_id in self._decisions:
            self._decisions[tc_id]["note"] = self._note_edit.toPlainText()

    def _apply_current(self) -> None:
        """상세 패널의 결정을 테이블 행에 반영."""
        row = self._table.currentRow()
        if row < 0:
            return
        tc_id = self._tcs[row].get("tc_id", f"__unknown_{row}__")
        dec = self._decisions.get(tc_id, {"status": "pending"})
        status = dec["status"]
        bg = _STATUS_COLORS.get(status, QColor("#ffffff"))
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(bg)
        status_item = self._table.item(row, 4)
        if status_item:
            status_item.setText(_STATUS_KO.get(status, status))
        self._update_summary()

    def _set_all(self, status: str) -> None:
        """모든 TC 상태 일괄 변경."""
        for tc_id in self._decisions:
            self._decisions[tc_id]["status"] = status
        bg = _STATUS_COLORS.get(status, QColor("#ffffff"))
        for r in range(self._table.rowCount()):
            for c in range(self._table.columnCount()):
                item = self._table.item(r, c)
                if item:
                    item.setBackground(bg)
            status_item = self._table.item(r, 4)
            if status_item:
                status_item.setText(_STATUS_KO.get(status, status))
        self._update_summary()

    def _update_summary(self) -> None:
        counts: dict[str, int] = {"approved": 0, "edited": 0, "rejected": 0, "pending": 0}
        for d in self._decisions.values():
            s = d.get("status", "pending")
            counts[s] = counts.get(s, 0) + 1
        self._summary_lbl.setText(
            f"총 {len(self._tcs)}건  |  "
            f"승인 {counts['approved']}  수정 {counts['edited']}  "
            f"거부 {counts['rejected']}  검토 전 {counts['pending']}"
        )

    def _export_excel(self) -> None:
        """현재 TC 목록(결정 반영)을 Excel 파일로 저장."""
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "TC 목록 저장",
            "tc_review.xlsx",
            "Excel 파일 (*.xlsx);;모든 파일 (*.*)",
        )
        if not save_path:
            return
        try:
            from app.tools.excel_builder import build_review
            tcs_with_decisions = []
            for tc in self._tcs:
                tc_id = tc.get("tc_id", "")
                dec = self._decisions.get(tc_id, {})
                tcs_with_decisions.append({
                    **tc,
                    "review_status": dec.get("status", "pending"),
                    "reviewer_note": dec.get("note", ""),
                    "reviewer_id":   dec.get("reviewer_id", ""),
                })
            build_review(tcs_with_decisions, save_path)
            QMessageBox.information(self, "저장 완료", f"저장되었습니다:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", str(e))

    def _submit(self) -> None:
        pending = sum(1 for d in self._decisions.values() if d["status"] == "pending")
        if pending > 0:
            res = QMessageBox.question(
                self, "확인",
                f"{pending}개 TC가 아직 '검토 전' 상태입니다. 그대로 완료하시겠습니까?\n"
                "(검토 전 TC는 Stage 5 자동 실행에서 제외됩니다.)",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.No:
                return
        self.decisions_ready.emit(self._decisions)
        self.accept()
