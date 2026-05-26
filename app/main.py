"""AWT 진입점 — PySide6 앱 초기화 및 창 연결 (D45, D46)."""
from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.auth.db_client import DBClient
from app.config.db_config import DBConfig
from app.config.settings import load_api_key, get_active_provider
from app.ui.login_window import LoginWindow
from app.ui.dashboard import Dashboard
from app.ui.wizard import RunWizard
from app.ui.pipeline_view import PipelineView
from app.ui.reviewer_gate import ReviewerGate
from app.ui.theme import APPLE_QSS


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("AWT")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    app.setStyleSheet(APPLE_QSS)

    # DB 설정
    db_cfg = DBConfig.from_env()
    db = DBClient(db_cfg)

    # ── 로그인 ────────────────────────────────────────────────────────────
    login = LoginWindow(db_config=db_cfg)

    token: str = ""
    username: str = ""
    api_key: str = ""
    role: str = "reviewer"

    def _on_logged_in(t: str, u: str, k: str) -> None:
        nonlocal token, username, api_key
        token, username, api_key = t, u, k
        session_info = db.validate_session(t)
        nonlocal role
        role = session_info["role"] if session_info else "reviewer"

    login.logged_in.connect(_on_logged_in)
    if login.exec() != LoginWindow.Accepted:
        sys.exit(0)

    # ── 대시보드 ──────────────────────────────────────────────────────────
    _pipeline_views: list[PipelineView] = []
    dash: Dashboard | None = None

    def _make_dashboard() -> None:
        nonlocal dash
        dash = Dashboard(token=token, username=username, role=role, api_key=api_key, db=db)
        dash.new_run_requested.connect(_open_wizard)
        dash.open_run_requested.connect(_reopen_run)
        dash.clone_run_requested.connect(_clone_run)
        dash.logout_requested.connect(_do_logout)
        dash.show()

    def _open_wizard() -> None:
        # 설정 탭에서 키를 저장한 경우를 위해 항상 최신값 로드
        current_key = load_api_key() or api_key
        if not current_key or current_key.startswith("AIza여기에") or current_key.startswith("sk-ant-여기에") or current_key.startswith("sk-여기에"):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                dash, "API Key 미설정",
                "LLM API Key가 설정되지 않았습니다.\n"
                "대시보드 → 설정 탭에서 API Key를 먼저 저장해주세요."
            )
            return
        wiz = RunWizard(api_key=current_key, parent=dash)
        wiz.run_config_ready.connect(_start_pipeline)
        wiz.exec()

    def _start_pipeline(config) -> None:
        pv = PipelineView(config=config, parent=None)
        _pipeline_views.append(pv)

        def _open_gate(tcs: list[dict]) -> None:
            try:
                gate = ReviewerGate(tcs=tcs, reviewer_id=username, parent=pv)
                gate.decisions_ready.connect(pv.apply_gate)
                gate.raise_()
                gate.activateWindow()
                gate.exec()
            except Exception:
                import traceback
                QMessageBox.critical(
                    pv, "Stage 4 오류",
                    traceback.format_exc()[:1200],
                )

        pv.gate_review_requested.connect(_open_gate)
        pv.show()

    def _reopen_run(run_id: str) -> None:
        """이력에서 기존 실행 재오픈 (결과 열람 전용)."""
        run_dir = Path("data/runs") / run_id
        tc_final = run_dir / "tc_final.xlsx"
        if tc_final.exists():
            import subprocess
            subprocess.Popen(["explorer", str(tc_final)])
        else:
            QMessageBox.information(
                dash, "알림",
                f"run_id={run_id} 의 tc_final.xlsx가 없습니다.\n"
                "진행 중인 실행은 Pipeline View에서 확인하세요."
            )

    def _clone_run(url: str) -> None:
        """이력 우클릭 → 복제: URL 클립보드 복사 + wizard prefill."""
        current_key = load_api_key() or api_key
        if not current_key or current_key.startswith("AIza여기에") or current_key.startswith("sk-ant-여기에") or current_key.startswith("sk-여기에"):
            QMessageBox.warning(
                dash, "API Key 미설정",
                "LLM API Key가 설정되지 않았습니다.\n"
                "대시보드 → 설정 탭에서 API Key를 먼저 저장해주세요."
            )
            return
        wiz = RunWizard(api_key=current_key, prefill_url=url, parent=dash)
        wiz.run_config_ready.connect(_start_pipeline)
        wiz.exec()

    def _do_logout() -> None:
        """로그아웃 → 대시보드 닫고 로그인 화면 재표시."""
        nonlocal token, username, api_key, role, dash
        if dash:
            dash.close()
            dash = None
        new_login = LoginWindow(db_config=db_cfg)
        new_login.logged_in.connect(_on_logged_in)
        if new_login.exec() == LoginWindow.Accepted:
            _make_dashboard()
        else:
            app.quit()

    _make_dashboard()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
