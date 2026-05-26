"""새 실행 마법사 (Step 1: URL·파일, Step 2: Auth, Step 3: 옵션) (D45: PySide6)."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QStackedWidget, QWidget, QCheckBox,
    QMessageBox, QGroupBox, QComboBox,
)

from app.config.settings import get_active_provider
from app.core.orchestrator import RunConfig

_MODELS: dict[str, list[tuple[str, str]]] = {
    "google": [
        # ── 무료 티어 있음 ──────────────────────────────────────────────
        ("gemini-2.5-flash",      "[무료] Gemini 2.5 Flash  — $0.30/$2.50/M  (추천)"),
        ("gemini-2.5-flash-lite", "[무료] Gemini 2.5 Flash Lite  — $0.10/$0.40/M  (저비용)"),
        ("gemini-2.5-pro",        "[무료] Gemini 2.5 Pro  — $1.25/$10.00/M  (고성능)"),
        # ── 유료 전용 ───────────────────────────────────────────────────
        ("gemini-3.1-flash-lite",  "[유료] Gemini 3.1 Flash Lite  — $0.25/$1.50/M"),
        ("gemini-3.5-flash",       "[유료] Gemini 3.5 Flash  — $1.50/$9.00/M"),
        ("gemini-3.1-pro-preview", "[유료] Gemini 3.1 Pro Preview  — $2.00/$12.00/M"),
        # ── 테스트 / 오픈소스 ────────────────────────────────────────────
        ("gemma-4-26b-a4b-it",     "[테스트] Gemma 4 26B  (gemma-4-26b-a4b-it)"),
    ],
    "anthropic": [
        # ── 유료 전용 (무료 API 티어 없음) ─────────────────────────────
        ("claude-haiku-4-5",   "[유료] Claude Haiku 4.5  — $1/$5/M  (저비용)"),
        ("claude-sonnet-4-6",  "[유료] Claude Sonnet 4.6  — $3/$15/M  (추천)"),
        ("claude-opus-4-7",    "[유료] Claude Opus 4.7  — $5/$25/M  (고성능)"),
    ],
    "openai": [
        # ── 유료 전용 (무료 API 티어 없음) ─────────────────────────────
        ("gpt-4.1-nano", "[유료] GPT-4.1 Nano  — $0.10/$0.40/M  (저비용)"),
        ("gpt-4o-mini",  "[유료] GPT-4o Mini  — $0.15/$0.60/M  (균형)"),
        ("gpt-4o",       "[유료] GPT-4o  — $2.50/$10.00/M  (고성능)"),
    ],
}


class RunWizard(QDialog):
    """3단계 마법사. run_config_ready(RunConfig) 시그널로 설정 전달."""

    run_config_ready = Signal(object)  # RunConfig

    def __init__(self, api_key: str, prefill_url: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 실행 — 설정 마법사")
        self.setFixedSize(620, 480)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._api_key = api_key
        self._auth_rows: list[dict] = []
        self._build_ui()
        # 복제 시 URL 자동 입력
        if prefill_url:
            self._url_edit.setText(prefill_url)

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # 단계 표시
        self._step_lbl = QLabel("Step 1 / 3")
        self._step_lbl.setStyleSheet(
            "font-weight:600; color:#0066cc; font-size:12px; letter-spacing:0.5px;"
        )
        root.addWidget(self._step_lbl)

        # 스택
        self._stack = QStackedWidget()
        self._stack.addWidget(self._page1())
        self._stack.addWidget(self._page2())
        self._stack.addWidget(self._page3())
        root.addWidget(self._stack)

        # 버튼
        btn_row = QHBoxLayout()
        self._back_btn = QPushButton("← 이전")
        self._back_btn.setEnabled(False)
        self._back_btn.clicked.connect(self._go_back)
        self._next_btn = QPushButton("다음 →")
        self._next_btn.clicked.connect(self._go_next)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._back_btn)
        btn_row.addWidget(self._next_btn)
        root.addLayout(btn_row)

    def _page1(self) -> QWidget:
        """대상 URL + 입력 파일."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(12)

        lay.addWidget(QLabel("<b>Step 1: 대상 URL과 요구사항 파일</b>"))

        url_box = QGroupBox("대상 웹 URL")
        url_lay = QVBoxLayout(url_box)
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://example.com")
        url_lay.addWidget(self._url_edit)
        lay.addWidget(url_box)

        file_box = QGroupBox("요구사항 파일 (PDF / DOCX / XLSX / MD, 복수 선택 가능)")
        file_lay = QVBoxLayout(file_box)
        self._file_list = QListWidget()
        self._file_list.setFixedHeight(120)
        file_lay.addWidget(self._file_list)
        add_btn = QPushButton("파일 추가…")
        add_btn.clicked.connect(self._add_files)
        remove_btn = QPushButton("선택 제거")
        remove_btn.clicked.connect(self._remove_file)
        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        file_lay.addLayout(btn_row)
        lay.addWidget(file_box)

        self._skip_stage0_cb = QCheckBox("Stage 0 DOM 스캔 건너뜀 (파일만 사용)")
        lay.addWidget(self._skip_stage0_cb)
        lay.addStretch()
        return w

    def _page2(self) -> QWidget:
        """인증 시퀀스 설정."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(12)

        lay.addWidget(QLabel("<b>Step 2: 인증 시퀀스 (선택)</b>"))
        lay.addWidget(QLabel(
            "로그인이 필요한 경우 아래에 단계를 추가하세요.\n"
            "action: goto | fill | click  /  selector: CSS 선택자  /  value: 입력값 (fill만)"
        ))

        self._auth_table = QTableWidget(0, 3)
        self._auth_table.setHorizontalHeaderLabels(["action", "selector", "value"])
        self._auth_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        lay.addWidget(self._auth_table)

        row_btns = QHBoxLayout()
        add_row = QPushButton("행 추가")
        add_row.clicked.connect(self._add_auth_row)
        del_row = QPushButton("행 삭제")
        del_row.clicked.connect(self._del_auth_row)
        row_btns.addWidget(add_row)
        row_btns.addWidget(del_row)
        row_btns.addStretch()
        lay.addLayout(row_btns)
        lay.addStretch()
        return w

    def _page3(self) -> QWidget:
        """실행 옵션."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)

        lay.addWidget(QLabel("<b>Step 3: 실행 옵션</b>"))

        # ── 모델 선택 ────────────────────────────────────────────────────
        model_box = QGroupBox("LLM 모델")
        m_lay = QVBoxLayout(model_box)
        self._model_combo = QComboBox()
        provider = get_active_provider()
        models = _MODELS.get(provider, [])
        for model_id, label in models:
            self._model_combo.addItem(label, userData=model_id)
        if not models:
            self._model_combo.addItem("(provider 미설정)", userData=None)
        m_lay.addWidget(self._model_combo)
        provider_hint = QLabel(f"현재 provider: {provider}")
        provider_hint.setStyleSheet("color:#888; font-size:11px;")
        m_lay.addWidget(provider_hint)
        lay.addWidget(model_box)

        # ── INFERRED 임계값 ──────────────────────────────────────────────
        thresh_box = QGroupBox("INFERRED 비율 임계값")
        t_lay = QVBoxLayout(thresh_box)
        self._thresh_spin = QDoubleSpinBox()
        self._thresh_spin.setRange(0.10, 0.80)
        self._thresh_spin.setSingleStep(0.05)
        self._thresh_spin.setValue(0.30)
        self._thresh_spin.setDecimals(2)
        self._thresh_spin.setSuffix("  (30% 권장)")
        t_lay.addWidget(self._thresh_spin)
        lay.addWidget(thresh_box)

        # ── 최대 기능 수 (max_leaves) ────────────────────────────────────
        leaves_box = QGroupBox("최대 분석 기능 수 (TC 설계)")
        l_lay = QVBoxLayout(leaves_box)
        self._max_leaves_spin = QSpinBox()
        self._max_leaves_spin.setRange(0, 9999)
        self._max_leaves_spin.setSingleStep(10)
        self._max_leaves_spin.setValue(50)
        self._max_leaves_spin.setSuffix("  개  (0 = 무제한)")
        l_lay.addWidget(self._max_leaves_spin)
        leaves_hint = QLabel(
            "무료 플랜(20회/일): 50개 이하 권장.  유료 플랜: 0으로 설정하면 전체 기능을 처리합니다."
        )
        leaves_hint.setWordWrap(True)
        leaves_hint.setStyleSheet("color:#888; font-size:11px;")
        l_lay.addWidget(leaves_hint)
        lay.addWidget(leaves_box)

        lay.addStretch()
        summary_lbl = QLabel("설정을 확인하고 '실행 시작'을 클릭하면 파이프라인이 시작됩니다.")
        summary_lbl.setWordWrap(True)
        summary_lbl.setStyleSheet("color:#555;")
        lay.addWidget(summary_lbl)
        return w

    # ── 네비게이션 ────────────────────────────────────────────────────────
    def _go_next(self) -> None:
        idx = self._stack.currentIndex()
        if idx == 0 and not self._validate_page1():
            return
        if idx == 1:
            self._collect_auth()
        if idx == 2:
            self._finish()
            return
        self._stack.setCurrentIndex(idx + 1)
        self._back_btn.setEnabled(True)
        if idx + 1 == 2:
            self._next_btn.setText("실행 시작")
        self._step_lbl.setText(f"Step {idx + 2} / 3")

    def _go_back(self) -> None:
        idx = self._stack.currentIndex()
        self._stack.setCurrentIndex(idx - 1)
        self._next_btn.setText("다음 →")
        self._back_btn.setEnabled(idx - 1 > 0)
        self._step_lbl.setText(f"Step {idx} / 3")

    def _validate_page1(self) -> bool:
        url = self._url_edit.text().strip()
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "입력 오류", "유효한 URL을 입력하세요 (http:// 또는 https://).")
            return False
        if self._file_list.count() == 0 and not self._skip_stage0_cb.isChecked():
            res = QMessageBox.question(
                self, "확인",
                "입력 파일이 없습니다. Stage 0 DOM 스캔만으로 진행하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.No:
                return False
        return True

    def _collect_auth(self) -> None:
        self._auth_rows = []
        for r in range(self._auth_table.rowCount()):
            action = (self._auth_table.item(r, 0) or QTableWidgetItem("")).text().strip()
            selector = (self._auth_table.item(r, 1) or QTableWidgetItem("")).text().strip()
            value = (self._auth_table.item(r, 2) or QTableWidgetItem("")).text().strip()
            if action:
                entry: dict = {"action": action, "selector": selector}
                if action == "fill":
                    entry["value"] = value
                elif action == "goto":
                    entry["url"] = selector
                self._auth_rows.append(entry)

    def _finish(self) -> None:
        model_override = self._model_combo.currentData()
        config = RunConfig(
            api_key=self._api_key,
            target_url=self._url_edit.text().strip(),
            input_files=[
                self._file_list.item(i).text()
                for i in range(self._file_list.count())
            ],
            auth_sequence=self._auth_rows,
            inferred_threshold=self._thresh_spin.value(),
            max_leaves=self._max_leaves_spin.value(),
            model_override=model_override,
        )
        self.run_config_ready.emit(config)
        self.accept()

    # ── 파일 목록 ─────────────────────────────────────────────────────────
    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "요구사항 파일 선택", "",
            "지원 파일 (*.pdf *.docx *.xlsx *.md *.txt);;All files (*)",
        )
        for p in paths:
            if not any(self._file_list.item(i).text() == p
                       for i in range(self._file_list.count())):
                self._file_list.addItem(p)

    def _remove_file(self) -> None:
        for item in self._file_list.selectedItems():
            self._file_list.takeItem(self._file_list.row(item))

    # ── 인증 테이블 ──────────────────────────────────────────────────────
    def _add_auth_row(self) -> None:
        r = self._auth_table.rowCount()
        self._auth_table.insertRow(r)
        self._auth_table.setItem(r, 0, QTableWidgetItem("fill"))

    def _del_auth_row(self) -> None:
        for item in self._auth_table.selectedItems():
            self._auth_table.removeRow(item.row())
