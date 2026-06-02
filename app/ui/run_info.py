"""실행 정보 다이얼로그 — 설정값 + 수집한 페이지 요소 조회/수정.

이력에서 연 run이 어떤 설정으로 실행됐고 어떤 페이지 요소를 수집했는지 확인하고,
필요하면 ① 설정을 복제해 수정·재실행 ② 수집 요소를 제외 저장할 수 있다.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QTreeWidget, QTreeWidgetItem,
    QWidget, QFileDialog, QMessageBox, QLineEdit,
)

# meta.json에서 보여줄 설정 (key, 한글 라벨)
_SETTING_ROWS = [
    ("run_id", "실행 ID"),
    ("created_at", "생성 시각"),
    ("stage", "마지막 단계"),
    ("target_url", "대상 URL"),
    ("model_override", "전역 모델"),
    ("model_overrides", "단계별 모델"),
    ("max_pages", "최대 페이지(BFS)"),
    ("max_leaves", "최대 기능 수"),
    ("concurrency", "동시성"),
    ("auto_pages", "페이지 자동 진행"),
    ("feature_gate", "기능 확정 게이트"),
    ("dedup_global_components", "전역 컴포넌트 dedup"),
    ("global_ratio", "전역 판정 임계"),
    ("headless_exec", "헤드리스 실행"),
    ("inferred_threshold", "INFERRED 임계"),
]


class RunInfoDialog(QDialog):
    """run_dir의 meta.json·feature-spec-draft.json을 조회/수정."""

    clone_requested = Signal(str)   # run_id → 설정 복제하여 재실행

    def __init__(self, run_dir, parent=None):
        super().__init__(parent)
        self._run_dir = Path(run_dir)
        self._run_id = self._run_dir.name
        self.setWindowTitle(f"실행 정보 — {self._run_id}")
        self.resize(820, 640)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._meta = self._load_json(self._run_dir / "meta.json") or {}
        self._draft_path = self._run_dir / "dom-scan" / "feature-spec-draft.json"
        self._draft = self._load_json(self._draft_path) or {}
        self._features = self._draft.get("features", []) or []

        self._build_ui()

    @staticmethod
    def _load_json(p: Path) -> dict | None:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        tabs = QTabWidget()
        tabs.addTab(self._build_settings_tab(), "⚙ 설정")
        tabs.addTab(self._build_features_tab(),
                    f"🧩 수집 페이지·요소 ({len(self._features)}개)")
        root.addWidget(tabs, stretch=1)

        bot = QHBoxLayout()
        clone_btn = QPushButton("⚙ 이 설정으로 복제·수정하여 재실행")
        clone_btn.setToolTip("이 실행의 설정을 그대로 가진 새 마법사를 열어 값을 수정한 뒤 재실행합니다.")
        clone_btn.clicked.connect(self._do_clone)
        bot.addWidget(clone_btn)
        bot.addStretch()
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        bot.addWidget(close_btn)
        root.addLayout(bot)

    # ── 설정 탭 ──────────────────────────────────────────────────────────
    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel("이 실행에 사용된 설정값입니다. (수정은 하단 '복제·재실행')"))
        tbl = QTableWidget(0, 2)
        tbl.setHorizontalHeaderLabels(["설정", "값"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.verticalHeader().setVisible(False)

        def _fmt(v):
            if isinstance(v, dict):
                return ", ".join(f"{k}={vv}" for k, vv in v.items()) or "(없음)"
            if isinstance(v, list):
                return f"{len(v)}개" if v else "(없음)"
            if v is None or v == "":
                return "(미설정)"
            return str(v)

        rows = list(_SETTING_ROWS)
        # 추가: 페이지/요소 수, 인증 여부, 커버리지
        extra = [
            ("__pages", "스캔 페이지 수", self._draft.get("pages_scanned", "?")),
            ("__feats", "수집 기능(요소) 수", len(self._features)),
            ("__auth", "인증 시퀀스", "있음" if self._meta.get("auth_sequence") else "없음"),
            ("__sel", "선택 URL 수", len(self._meta.get("selected_urls") or [])),
        ]
        for key, label in rows:
            r = tbl.rowCount(); tbl.insertRow(r)
            tbl.setItem(r, 0, QTableWidgetItem(label))
            tbl.setItem(r, 1, QTableWidgetItem(_fmt(self._meta.get(key))))
        for _k, label, val in extra:
            r = tbl.rowCount(); tbl.insertRow(r)
            tbl.setItem(r, 0, QTableWidgetItem(label))
            tbl.setItem(r, 1, QTableWidgetItem(_fmt(val)))
        # 커버리지/리포트 요약
        cov = self._meta.get("coverage") or {}
        if cov:
            r = tbl.rowCount(); tbl.insertRow(r)
            tbl.setItem(r, 0, QTableWidgetItem("커버리지"))
            tbl.setItem(r, 1, QTableWidgetItem(
                f"{cov.get('coverage_pct','?')}% (기능 {cov.get('designed_features','?')}/{cov.get('total_unique_features','?')}, TC {cov.get('total_tcs','?')})"))
        lay.addWidget(tbl)
        return w

    # ── 수집 페이지·요소 탭 ───────────────────────────────────────────────
    def _build_features_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel(
            "수집된 페이지별 요소(기능)입니다. 제외할 항목의 체크를 해제하고 '변경 저장'을 누르면 "
            "feature-spec-draft.json에 반영됩니다(이후 Stage 1부터 재개 시 적용)."))

        # 검색
        srow = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("기능명·URL 검색…")
        self._search.textChanged.connect(self._filter_tree)
        srow.addWidget(self._search)
        for label, fn in [("모두 펼치기", lambda: self._tree.expandAll()),
                          ("모두 접기", lambda: self._tree.collapseAll())]:
            b = QPushButton(label); b.clicked.connect(fn); srow.addWidget(b)
        lay.addLayout(srow)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(["페이지 / 기능 (대>중>소)", "근거 요소", "신뢰도"])
        self._tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tree.setColumnWidth(1, 200)
        self._populate_tree()
        lay.addWidget(self._tree, stretch=1)

        brow = QHBoxLayout()
        save_btn = QPushButton("💾 변경 저장 (제외 반영)")
        save_btn.clicked.connect(self._save_features)
        brow.addWidget(save_btn)
        xlsx_btn = QPushButton("⬇ Excel 내보내기")
        xlsx_btn.clicked.connect(self._export_excel)
        brow.addWidget(xlsx_btn)
        brow.addStretch()
        self._feat_summary = QLabel("")
        brow.addWidget(self._feat_summary)
        lay.addLayout(brow)
        self._update_feat_summary()
        return w

    def _populate_tree(self) -> None:
        groups: "OrderedDict[str, list[int]]" = OrderedDict()
        for idx, f in enumerate(self._features):
            url = f.get("source_url", "") or "(미상)"
            groups.setdefault(url, []).append(idx)
        self._tree.blockSignals(True)
        for url, idxs in groups.items():
            parent = QTreeWidgetItem(self._tree)
            parent.setText(0, f"{url}   ·   {len(idxs)}개")
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            parent.setCheckState(0, Qt.Checked)
            parent.setData(0, Qt.UserRole, None)
            for idx in idxs:
                f = self._features[idx]
                child = QTreeWidgetItem(parent)
                child.setText(0, f"{f.get('category_major','')} > {f.get('category_mid','')} > {f.get('category_leaf','')}")
                child.setText(1, str(f.get("source_element", "")))
                child.setText(2, str(f.get("confidence", "")))
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Checked)
                child.setData(0, Qt.UserRole, idx)
        self._tree.blockSignals(False)
        self._tree.collapseAll()
        self._tree.itemChanged.connect(lambda *_: self._update_feat_summary())

    def _filter_tree(self, text: str) -> None:
        text = (text or "").lower().strip()
        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            any_visible = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                hit = (not text) or text in child.text(0).lower()
                child.setHidden(not hit)
                any_visible = any_visible or hit
            url_hit = (not text) or text in parent.text(0).lower()
            parent.setHidden(not (any_visible or url_hit))
            if text and any_visible:
                parent.setExpanded(True)

    def _kept_indices(self) -> list[int]:
        kept = []
        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    idx = child.data(0, Qt.UserRole)
                    if idx is not None:
                        kept.append(idx)
        return kept

    def _update_feat_summary(self) -> None:
        kept = len(self._kept_indices())
        total = len(self._features)
        self._feat_summary.setText(f"유지 {kept} / 전체 {total}  (제외 {total - kept})")

    def _save_features(self) -> None:
        kept = set(self._kept_indices())
        new_feats = [f for i, f in enumerate(self._features) if i in kept]
        if not new_feats:
            QMessageBox.warning(self, "저장 불가", "최소 1개 이상 유지해야 합니다.")
            return
        if not self._draft_path.exists():
            QMessageBox.warning(self, "저장 불가", "feature-spec-draft.json이 없습니다.")
            return
        self._draft["features"] = new_feats
        self._draft_path.write_text(
            json.dumps(self._draft, ensure_ascii=False, indent=2), encoding="utf-8")
        self._features = new_feats
        QMessageBox.information(
            self, "저장 완료",
            f"{len(new_feats)}개 요소로 저장했습니다.\n"
            "이 실행을 'Stage 1부터 재개'하면 반영됩니다.")
        # 트리 재구성
        self._tree.clear()
        self._populate_tree()
        self._update_feat_summary()

    def _export_excel(self) -> None:
        if not self._features:
            QMessageBox.information(self, "알림", "내보낼 요소가 없습니다.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "기능 목록 저장", f"features_{self._run_id}.xlsx",
            "Excel 파일 (*.xlsx)")
        if not path:
            return
        try:
            from app.tools.excel_builder import build_features
            build_features(self._features, path)
            QMessageBox.information(self, "저장 완료", path)
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", str(e))

    def _do_clone(self) -> None:
        self.clone_requested.emit(self._run_id)
        self.accept()
