"""대시보드 창 — 실행 이력·사용자 관리·설정 (D45: PySide6)."""
from __future__ import annotations
import json
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QLineEdit, QComboBox, QMessageBox,
    QHeaderView, QFrame, QStatusBar, QMenu, QApplication,
)

from app.auth.db_client import DBClient
from app.config.settings import (
    save_api_key, load_api_key, delete_api_key,
    get_active_provider, set_active_provider, VALID_PROVIDERS,
)

# Provider 표시 라벨 (UI용)
_PROVIDER_LABELS = {
    "anthropic": "Anthropic (Claude)",
    "openai":    "OpenAI (GPT)",
    "google":    "Google (Gemini)",
}
_PROVIDER_PLACEHOLDERS = {
    "anthropic": "sk-ant-...",
    "openai":    "sk-...",
    "google":    "AIza...",
}

RUNS_DIR = Path("data/runs")


class Dashboard(QMainWindow):
    """로그인 후 첫 화면. 새 실행, 이력 조회, 설정."""

    new_run_requested = Signal()       # → wizard 열기
    open_run_requested = Signal(str)   # run_id → pipeline_view 열기
    clone_run_requested = Signal(str)  # url → wizard(prefill) 열기
    logout_requested = Signal()        # → 로그아웃

    def __init__(
        self,
        token: str,
        username: str,
        role: str,
        api_key: str,
        db: DBClient,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"AWT 대시보드 — {username}")
        self.resize(900, 580)
        self._token = token
        self._username = username
        self._role = role
        self._api_key = api_key
        self._db = db

        self._build_ui()
        self._load_runs()

    # ── UI 구성 ──────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        central.setStyleSheet("QWidget#dash_central { background-color: #f1f5f9; }")
        central.setObjectName("dash_central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 상단 헤더 (global-nav) ────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet("QFrame { background: #000000; border: none; }")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        h_lay.setSpacing(0)

        lbl = QLabel("AWT")
        lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl.setStyleSheet("color: #ffffff; background: transparent; border: none; letter-spacing: 1px;")
        h_lay.addWidget(lbl)
        h_lay.addStretch()

        user_lbl = QLabel(f"{self._username}  ·  {self._role}")
        user_lbl.setStyleSheet(
            "color: #64748b; font-size: 12px; background: transparent; border: none;"
        )
        h_lay.addWidget(user_lbl)
        h_lay.addSpacing(16)

        logout_btn = QPushButton("로그아웃")
        logout_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #64748b; border: none;"
            " border-radius: 0; padding: 0 4px; font-size: 12px; min-height: 0; }"
            "QPushButton:hover { color: #ffffff; }"
        )
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested)
        h_lay.addWidget(logout_btn)
        root.addWidget(header)

        # ── 탭 ───────────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(
            "QTabWidget::pane { background: #f1f5f9; border: none; }"
            "QTabBar::tab { background: transparent; color: #64748b;"
            " padding: 10px 20px; font-size: 13px; font-weight: 500;"
            " border: none; border-bottom: 2px solid transparent; }"
            "QTabBar::tab:selected { color: #3b82f6;"
            " border-bottom: 2px solid #3b82f6; font-weight: 600; }"
            "QTabBar::tab:hover { color: #1e293b; }"
            "QTabWidget > QWidget { background: #f1f5f9; }"
        )
        root.addWidget(tabs)

        tabs.addTab(self._build_runs_tab(), "실행 이력")
        tabs.addTab(self._build_settings_tab(), "설정")
        if self._role == "admin":
            tabs.addTab(self._build_users_tab(), "사용자 관리")

        # 상태바
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("준비")

    def _build_runs_tab(self) -> QWidget:
        outer = QWidget()
        outer.setStyleSheet("background: #f1f5f9;")
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(12, 12, 12, 12)
        outer_lay.setSpacing(8)

        # 카드
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #ffffff; border-radius: 8px;"
            " border: 1px solid #e2e8f0; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        # 상단: 제목 + 새로고침 + 새 실행 버튼
        top = QHBoxLayout()
        hdr = QLabel("실행 이력")
        hdr.setStyleSheet(
            "QLabel { background: transparent; border: none;"
            " font-size: 15px; font-weight: 700; color: #1e293b; }"
        )
        top.addWidget(hdr)
        top.addStretch()

        refresh_btn = QPushButton("↺  새로고침")
        refresh_btn.setFixedHeight(34)
        refresh_btn.setStyleSheet(
            "QPushButton { background: #ffffff; color: #64748b;"
            " border-radius: 6px; padding: 0 14px; font-size: 13px;"
            " font-weight: 600; border: 1px solid #e2e8f0; }"
            "QPushButton:hover { background: #f8fafc; color: #1e293b; }"
        )
        refresh_btn.clicked.connect(self._load_runs)
        top.addWidget(refresh_btn)
        top.addSpacing(8)

        self._new_btn = QPushButton("＋  새 실행")
        self._new_btn.setFixedHeight(34)
        self._new_btn.setStyleSheet(
            "QPushButton { background: #3b82f6; color: #ffffff;"
            " border-radius: 6px; padding: 0 16px; font-size: 13px;"
            " font-weight: 600; border: none; }"
            "QPushButton:hover { background: #2563eb; }"
        )
        self._new_btn.clicked.connect(self.new_run_requested)
        top.addWidget(self._new_btn)
        lay.addLayout(top)

        # 테이블
        self._runs_table = QTableWidget(0, 5)
        self._runs_table.setHorizontalHeaderLabels(["Run ID", "대상 URL", "TC 수", "단계", "일시"])
        self._runs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._runs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._runs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._runs_table.doubleClicked.connect(self._open_run)
        self._runs_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._runs_table.customContextMenuRequested.connect(self._on_runs_context_menu)
        self._runs_table.setStyleSheet(
            "QTableWidget { border: none; background: #ffffff; }"
            "QHeaderView::section { background-color: #f8fafc; color: #64748b;"
            " font-size: 12px; font-weight: 600; padding: 7px 8px;"
            " border: none; border-bottom: 1px solid #e2e8f0; }"
            "QTableWidget::item { border-bottom: 1px solid #f1f5f9;"
            " padding: 6px 8px; color: #334155; }"
            "QTableWidget::item:selected { background: #eff6ff; color: #1e293b; }"
        )
        lay.addWidget(self._runs_table)
        outer_lay.addWidget(card)
        return outer

    def _build_settings_tab(self) -> QWidget:
        outer = QWidget()
        outer.setStyleSheet("background: #f1f5f9;")
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(12, 12, 12, 12)
        outer_lay.setSpacing(8)

        # 카드
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #ffffff; border-radius: 8px;"
            " border: 1px solid #e2e8f0; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(14)

        hdr = QLabel("API 설정")
        hdr.setStyleSheet(
            "QLabel { background: transparent; border: none;"
            " font-size: 15px; font-weight: 700; color: #1e293b;"
            " padding-bottom: 4px; border-bottom: 1px solid #f1f5f9; }"
        )
        lay.addWidget(hdr)

        # ── Provider 선택 ─────────────────────────────────────────────────
        lbl_prov = QLabel("LLM Provider")
        lbl_prov.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: 600; color: #374151;"
            " background: transparent; border: none; }"
        )
        lay.addWidget(lbl_prov)
        self._provider_combo = QComboBox()
        for p in VALID_PROVIDERS:
            self._provider_combo.addItem(_PROVIDER_LABELS[p], userData=p)
        current = get_active_provider()
        idx = list(VALID_PROVIDERS).index(current) if current in VALID_PROVIDERS else 0
        self._provider_combo.setCurrentIndex(idx)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        lay.addWidget(self._provider_combo)

        # ── API Key ───────────────────────────────────────────────────────
        self._api_label = QLabel(f"{_PROVIDER_LABELS[current]} API Key")
        self._api_label.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: 600; color: #374151;"
            " background: transparent; border: none; }"
        )
        lay.addWidget(self._api_label)

        api_row = QHBoxLayout()
        api_row.setSpacing(8)
        self._api_edit = QLineEdit(load_api_key(current) or "")
        self._api_edit.setEchoMode(QLineEdit.Password)
        self._api_edit.setPlaceholderText(_PROVIDER_PLACEHOLDERS[current])
        self._api_edit.setFixedHeight(36)
        api_row.addWidget(self._api_edit)

        _btn_style = (
            "QPushButton { border-radius: 6px; padding: 0 14px; font-size: 12px;"
            " font-weight: 600; height: 36px; }"
        )
        save_btn = QPushButton("저장")
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(
            _btn_style +
            "QPushButton { background: #3b82f6; color: #fff; border: none; }"
            "QPushButton:hover { background: #2563eb; }"
        )
        save_btn.clicked.connect(self._save_api_key)
        api_row.addWidget(save_btn)

        del_btn = QPushButton("삭제")
        del_btn.setFixedHeight(36)
        del_btn.setStyleSheet(
            _btn_style +
            "QPushButton { background: #fff; color: #ef4444;"
            " border: 1px solid #fca5a5; }"
            "QPushButton:hover { background: #fee2e2; }"
        )
        del_btn.clicked.connect(self._delete_api_key)
        api_row.addWidget(del_btn)
        lay.addLayout(api_row)

        # 안내
        hint = QLabel(
            "Provider별 API 키는 각각 따로 저장됩니다. Provider 전환 시 해당 키만 사용됩니다.\n"
            "모델은 prompts/*.md 의 model 필드(claude-* / gpt-* / gemini-*)로 결정됩니다."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "QLabel { color: #94a3b8; font-size: 11px;"
            " background: transparent; border: none; }"
        )
        lay.addWidget(hint)
        lay.addStretch()

        outer_lay.addWidget(card)
        outer_lay.addStretch()
        return outer

    def _on_provider_changed(self, index: int) -> None:
        """Provider 드롭다운 변경 시 — 활성 provider 갱신 + 해당 키 로드."""
        provider = self._provider_combo.itemData(index)
        if not provider:
            return
        set_active_provider(provider)
        self._api_label.setText(f"{_PROVIDER_LABELS[provider]} API Key")
        self._api_edit.setText(load_api_key(provider) or "")
        self._api_edit.setPlaceholderText(_PROVIDER_PLACEHOLDERS[provider])
        self.statusBar().showMessage(f"Provider 전환: {_PROVIDER_LABELS[provider]}", 3000)

    def _build_users_tab(self) -> QWidget:
        """admin 전용 사용자 관리 탭."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        form = QHBoxLayout()
        self._new_user_edit = QLineEdit()
        self._new_user_edit.setPlaceholderText("사용자명")
        self._new_pw_edit = QLineEdit()
        self._new_pw_edit.setPlaceholderText("초기 비밀번호")
        self._new_pw_edit.setEchoMode(QLineEdit.Password)
        self._role_combo = QComboBox()
        self._role_combo.addItems(["reviewer", "admin"])
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self._add_user)
        form.addWidget(self._new_user_edit)
        form.addWidget(self._new_pw_edit)
        form.addWidget(self._role_combo)
        form.addWidget(add_btn)
        lay.addLayout(form)

        self._users_table = QTableWidget(0, 3)
        self._users_table.setHorizontalHeaderLabels(["사용자명", "역할", "생성일"])
        self._users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self._users_table)

        del_btn2 = QPushButton("선택 사용자 삭제")
        del_btn2.clicked.connect(self._delete_user)
        lay.addWidget(del_btn2, alignment=Qt.AlignRight)

        self._refresh_users()
        return w

    # ── 데이터 로딩 ──────────────────────────────────────────────────────
    def _load_runs(self) -> None:
        self._runs_table.setRowCount(0)
        if not RUNS_DIR.exists():
            return
        runs = sorted(RUNS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for run_dir in runs[:50]:
            meta_path = run_dir / "meta.json"
            meta: dict = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            tc_count = "?"
            tc_path = run_dir / "tc_raw.json"
            if tc_path.exists():
                try:
                    tc_count = str(len(json.loads(tc_path.read_text(encoding="utf-8"))))
                except Exception:
                    pass
            row = self._runs_table.rowCount()
            self._runs_table.insertRow(row)
            self._runs_table.setItem(row, 0, QTableWidgetItem(run_dir.name))
            self._runs_table.setItem(row, 1, QTableWidgetItem(meta.get("target_url", "-")))
            self._runs_table.setItem(row, 2, QTableWidgetItem(tc_count))
            self._runs_table.setItem(row, 3, QTableWidgetItem(meta.get("stage", "-")))
            self._runs_table.setItem(row, 4, QTableWidgetItem(meta.get("created_at", "-")))

    def _open_run(self) -> None:
        row = self._runs_table.currentRow()
        if row < 0:
            return
        run_id = self._runs_table.item(row, 0).text()
        self.open_run_requested.emit(run_id)

    def _on_runs_context_menu(self, pos) -> None:
        """우클릭 컨텍스트 메뉴 — 복제."""
        row = self._runs_table.rowAt(pos.y())
        if row < 0:
            return
        url_item = self._runs_table.item(row, 1)
        url = url_item.text() if url_item else ""
        has_url = bool(url) and url != "-"

        menu = QMenu(self)
        clone_action = menu.addAction("복제")
        clone_action.setEnabled(has_url)

        action = menu.exec(self._runs_table.viewport().mapToGlobal(pos))
        if action == clone_action and has_url:
            QApplication.clipboard().setText(url)
            self.clone_run_requested.emit(url)
            self.statusBar().showMessage(f"URL 복사됨: {url}", 3000)

    # ── 설정 액션 ────────────────────────────────────────────────────────
    def _save_api_key(self) -> None:
        provider = self._provider_combo.currentData()
        key = self._api_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "경고", "API Key가 비어있습니다.")
            return
        save_api_key(key, provider=provider)
        self.statusBar().showMessage(
            f"{_PROVIDER_LABELS[provider]} API Key 저장 완료", 3000
        )

    def _delete_api_key(self) -> None:
        provider = self._provider_combo.currentData()
        delete_api_key(provider=provider)
        self._api_edit.clear()
        self.statusBar().showMessage(
            f"{_PROVIDER_LABELS[provider]} API Key 삭제 완료", 3000
        )

    # ── 사용자 관리 액션 ──────────────────────────────────────────────────
    def _refresh_users(self) -> None:
        try:
            users = self._db.list_users()
        except Exception:
            return
        self._users_table.setRowCount(0)
        for u in users:
            row = self._users_table.rowCount()
            self._users_table.insertRow(row)
            self._users_table.setItem(row, 0, QTableWidgetItem(u["username"]))
            self._users_table.setItem(row, 1, QTableWidgetItem(u["role"]))
            self._users_table.setItem(row, 2, QTableWidgetItem(str(u.get("created_at", ""))))

    def _add_user(self) -> None:
        username = self._new_user_edit.text().strip()
        password = self._new_pw_edit.text()
        role = self._role_combo.currentText()
        if not username or not password:
            QMessageBox.warning(self, "입력 오류", "사용자명과 비밀번호를 입력하세요.")
            return
        try:
            self._db.create_user(username, password, role)
            self._new_user_edit.clear()
            self._new_pw_edit.clear()
            self._refresh_users()
        except ValueError as e:
            QMessageBox.warning(self, "오류", str(e))

    def _delete_user(self) -> None:
        row = self._users_table.currentRow()
        if row < 0:
            return
        username = self._users_table.item(row, 0).text()
        if username == self._username:
            QMessageBox.warning(self, "오류", "본인 계정은 삭제할 수 없습니다.")
            return
        confirmed = QMessageBox.question(
            self, "확인", f"'{username}'을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirmed == QMessageBox.Yes:
            self._db.delete_user(username)
            self._refresh_users()
