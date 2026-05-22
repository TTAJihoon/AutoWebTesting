"""로그인 창 (D40: PostgreSQL 인증, D45: PySide6)."""
from __future__ import annotations
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox,
)

from app.auth.db_client import DBClient
from app.config.db_config import DBConfig
from app.config.settings import load_api_key


class _LoginWorker(QThread):
    success = Signal(str, str)   # token, username
    failure = Signal(str)        # error message

    def __init__(self, username: str, password: str, db: DBClient):
        super().__init__()
        self._username = username
        self._password = password
        self._db = db

    def run(self) -> None:
        try:
            token = self._db.login(self._username, self._password)
            if token:
                self.success.emit(token, self._username)
            else:
                self.failure.emit("아이디 또는 비밀번호가 올바르지 않습니다.")
        except Exception as e:
            self.failure.emit(f"DB 연결 오류: {e}")


class LoginWindow(QDialog):
    """로그인 성공 시 token, username, api_key를 반환."""

    logged_in = Signal(str, str, str)  # token, username, api_key

    def __init__(self, db_config: DBConfig | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AWT — 로그인")
        self.setFixedSize(380, 320)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._db = DBClient(db_config)
        self._worker: _LoginWorker | None = None

        self._build_ui()
        self._check_db_available()

    def _build_ui(self) -> None:
        self.setStyleSheet("QDialog{background:#000000;}")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── 상단 다크 헤더 영역 ─────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(160)
        header.setStyleSheet("background:#000000;")
        h_lay = QVBoxLayout(header)
        h_lay.setAlignment(Qt.AlignCenter)
        h_lay.setSpacing(4)

        title = QLabel("AWT")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffffff; background:transparent;")
        h_lay.addWidget(title)

        subtitle = QLabel("AI-driven Web Testing")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color:#7a7a7a; font-size:13px; background:transparent;")
        h_lay.addWidget(subtitle)
        layout.addWidget(header)

        # ── 폼 영역 ─────────────────────────────────────────────────────
        form = QWidget()
        form.setStyleSheet("background:#f5f5f7;")
        f_lay = QVBoxLayout(form)
        f_lay.setContentsMargins(40, 28, 40, 28)
        f_lay.setSpacing(10)

        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("사용자 ID")
        self._user_edit.setFixedHeight(38)
        f_lay.addWidget(self._user_edit)

        self._pw_edit = QLineEdit()
        self._pw_edit.setPlaceholderText("비밀번호")
        self._pw_edit.setEchoMode(QLineEdit.Password)
        self._pw_edit.setFixedHeight(38)
        self._pw_edit.returnPressed.connect(self._do_login)
        f_lay.addWidget(self._pw_edit)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(
            "color:#cc0000; font-size:12px; background:transparent;"
        )
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setWordWrap(True)
        f_lay.addWidget(self._status_lbl)

        self._login_btn = QPushButton("로그인")
        self._login_btn.setFixedHeight(40)
        self._login_btn.clicked.connect(self._do_login)
        f_lay.addWidget(self._login_btn)

        layout.addWidget(form)

    def _check_db_available(self) -> None:
        if not DBClient.is_available():
            self._status_lbl.setText("⚠ DB에 연결할 수 없습니다. 네트워크를 확인하세요.")
            self._login_btn.setEnabled(False)

    def _do_login(self) -> None:
        username = self._user_edit.text().strip()
        password = self._pw_edit.text()
        if not username or not password:
            self._status_lbl.setText("아이디와 비밀번호를 입력하세요.")
            return

        self._login_btn.setEnabled(False)
        self._login_btn.setText("로그인 중…")
        self._status_lbl.setText("")

        self._worker = _LoginWorker(username, password, self._db)
        self._worker.success.connect(self._on_success)
        self._worker.failure.connect(self._on_failure)
        self._worker.start()

    def _on_success(self, token: str, username: str) -> None:
        api_key = load_api_key() or ""
        self.logged_in.emit(token, username, api_key)
        self.accept()

    def _on_failure(self, msg: str) -> None:
        self._status_lbl.setText(msg)
        self._login_btn.setEnabled(True)
        self._login_btn.setText("로그인")
        self._pw_edit.clear()
        self._pw_edit.setFocus()
