"""Stage 1.5 — 기능 확정 게이트 (D53).

Stage 1b(기능 통합) 완료 후 Stage 2(TC 설계) 진입 전, 사용자가 도메인별 기능
집계를 보고 ① 비대한 도메인을 펼쳐 ② 불필요한 leaf를 제외할 수 있는 선택적 게이트.

- 기본값: 전부 유지(무조작 통과) → 회귀 없음.
- 대분류(통제 어휘, D52)별로 묶어 집계 → 어느 도메인이 과대표집인지 한눈에.
- 제외한 leaf는 Stage 2에서 TC 설계 대상에서 빠짐(추적성: meta.json 기록).
"""
from __future__ import annotations

from collections import OrderedDict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QFrame, QHeaderView, QWidget,
)

_CARD = (
    "QFrame { background-color: #ffffff; border-radius: 8px;"
    " border: 1px solid #e2e8f0; }"
)


class FeatureGate(QDialog):
    """도메인별 기능 집계 + leaf 제외. exec() 후 self.kept_leaves 사용."""

    def __init__(self, leaves: list[dict], parent=None):
        super().__init__(parent)
        self._leaves = leaves or []
        # 기본: 전부 유지 (사용자가 아무 것도 안 건드리면 회귀 없음)
        self.kept_leaves: list[dict] = list(self._leaves)
        self.excluded_count: int = 0

        self.setWindowTitle("기능 확정 — Stage 2(TC 설계) 진행 전")
        self.resize(740, 660)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet("QDialog { background-color: #f1f5f9; }")

        self._build_ui()
        self._populate()
        self._update_summary()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        title = QLabel(
            "<b style='font-size:15px; color:#1e293b;'>기능 확정</b>"
            "<span style='color:#64748b; font-size:12px;'>  — TC를 설계할 기능을 확인하고,"
            " 불필요한 기능은 체크 해제하세요. (그대로 두면 전부 진행)</span>"
        )
        root.addWidget(title)

        self._summary_lbl = QLabel()
        self._summary_lbl.setStyleSheet("color:#64748b; font-size:12px;")
        root.addWidget(self._summary_lbl)

        # 트리: 도메인(대분류) > leaf
        card = QFrame()
        card.setStyleSheet(_CARD)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(8, 8, 8, 8)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(["기능 (대분류 > 중분류 > 소분류)", "비중"])
        self._tree.setStyleSheet(
            "QTreeWidget { border: none; background: #ffffff; font-size: 12px; }"
            "QHeaderView::section { background:#f8fafc; color:#64748b; font-weight:600;"
            " border:none; border-bottom:1px solid #e2e8f0; padding:6px 8px; }"
        )
        hh = self._tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Fixed)
        self._tree.setColumnWidth(1, 90)
        self._tree.itemChanged.connect(self._on_item_changed)
        card_lay.addWidget(self._tree)
        root.addWidget(card, stretch=1)

        # 펼치기/접기 + 전체 선택/해제
        ctl = QHBoxLayout()
        for label, fn in [
            ("모두 펼치기", self._tree.expandAll),
            ("모두 접기",   self._tree.collapseAll),
        ]:
            b = QPushButton(label)
            b.setFixedHeight(28)
            b.setStyleSheet(
                "QPushButton { background:#ffffff; color:#475569; border:1px solid #e2e8f0;"
                " border-radius:6px; padding:0 12px; font-size:12px; }"
                "QPushButton:hover { background:#f8fafc; }"
            )
            b.clicked.connect(fn)
            ctl.addWidget(b)
        ctl.addStretch()
        root.addLayout(ctl)

        # 하단 버튼
        bot = QHBoxLayout()
        cancel = QPushButton("취소")
        cancel.setFixedHeight(36)
        cancel.setStyleSheet(
            "QPushButton { background:#ffffff; color:#64748b; border:1px solid #e2e8f0;"
            " border-radius:6px; padding:0 18px; font-size:13px; }"
            "QPushButton:hover { background:#f8fafc; }"
        )
        cancel.clicked.connect(self.reject)

        self._confirm_btn = QPushButton("확정 → Stage 2 진행")
        self._confirm_btn.setFixedHeight(36)
        self._confirm_btn.setStyleSheet(
            "QPushButton { background:#7c3aed; color:#ffffff; border:none;"
            " border-radius:6px; padding:0 20px; font-size:13px; font-weight:600; }"
            "QPushButton:hover { background:#6d28d9; }"
        )
        self._confirm_btn.clicked.connect(self._confirm)

        bot.addWidget(cancel)
        bot.addStretch()
        bot.addWidget(self._confirm_btn)
        root.addLayout(bot)

    def _populate(self) -> None:
        # 대분류 → leaf 인덱스 목록 (등장 순 유지, 개수 많은 도메인 먼저)
        groups: "OrderedDict[str, list[int]]" = OrderedDict()
        for idx, lf in enumerate(self._leaves):
            maj = (lf.get("category_major", "") or "기타")
            groups.setdefault(maj, []).append(idx)

        total = max(len(self._leaves), 1)
        self._tree.blockSignals(True)
        for maj, idxs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            pct = len(idxs) / total * 100
            parent = QTreeWidgetItem(self._tree)
            parent.setText(0, f"{maj}  ·  기능 {len(idxs)}개")
            parent.setText(1, f"{pct:.1f}%")
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            parent.setCheckState(0, Qt.Checked)
            parent.setData(0, Qt.UserRole, None)   # 도메인 노드 표식
            f = parent.font(0); f.setBold(True); parent.setFont(0, f)

            for idx in idxs:
                lf = self._leaves[idx]
                mid = lf.get("category_mid", "") or "-"
                leaf = lf.get("category_leaf", "") or "-"
                child = QTreeWidgetItem(parent)
                child.setText(0, f"{mid} > {leaf}")
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Checked)
                child.setData(0, Qt.UserRole, idx)   # leaf 원본 인덱스
        self._tree.blockSignals(False)
        self._tree.expandAll()

    # ── 이벤트 ──────────────────────────────────────────────────────────────
    def _on_item_changed(self, item: QTreeWidgetItem, col: int) -> None:
        if col != 0:
            return
        self._update_summary()

    def _checked_leaf_indices(self) -> list[int]:
        kept: list[int] = []
        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    idx = child.data(0, Qt.UserRole)
                    if idx is not None:
                        kept.append(idx)
        return kept

    def _update_summary(self) -> None:
        kept = len(self._checked_leaf_indices())
        total = len(self._leaves)
        excluded = total - kept
        self._summary_lbl.setText(
            f"전체 기능 {total}개  |  유지 {kept}개  |  제외 {excluded}개"
            + ("   ⚠ 제외된 기능은 TC 설계에서 빠집니다." if excluded else "")
        )

    def _confirm(self) -> None:
        kept_idx = self._checked_leaf_indices()
        self.kept_leaves = [self._leaves[i] for i in kept_idx]
        self.excluded_count = len(self._leaves) - len(self.kept_leaves)
        self.accept()
