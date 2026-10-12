from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QMenu,
    QSystemTrayIcon,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from seewhatisee.ai import VisionError, VisionService
from seewhatisee.capture import CaptureError, ScreenCapture
from seewhatisee.config import Settings
from seewhatisee.ui.hotkey import GlobalHotkey


class AnswerSignals(QWidget):
    completed = Signal(str)
    failed = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings.from_environment()
        self.capture = ScreenCapture()
        self.image = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.signals = AnswerSignals()
        self.signals.completed.connect(self._show_answer)
        self.signals.failed.connect(self._show_error)
        self.current_answer = ""
        self._quitting = False
        self.setWindowTitle("SeeWhatISee")
        self.setMinimumSize(1120, 760)
        self._build_ui()
        self._apply_style()
        self.hotkey = GlobalHotkey()
        application = QApplication.instance()
        if application is not None:
            application.installNativeEventFilter(self.hotkey)
        self.hotkey.pressed.connect(self._capture_from_hotkey)
        if not self.hotkey.register():
            self.hotkey_status = "Keyboard shortcut unavailable"
        self._setup_tray()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(24, 26, 24, 24)
        sidebar_layout.setSpacing(12)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        brand_mark = QLabel("S")
        brand_mark.setObjectName("brandMark")
        brand_name = QLabel("SeeWhatISee")
        brand_name.setObjectName("brandName")
        brand_row.addWidget(brand_mark)
        brand_row.addWidget(brand_name)
        brand_row.addStretch()
        sidebar_layout.addLayout(brand_row)

        sidebar_layout.addSpacing(34)
        nav_caption = QLabel("YOUR WORKSPACE")
        nav_caption.setObjectName("sideCaption")
        sidebar_layout.addWidget(nav_caption)
        workspace_item = QLabel("  Workspace")
        workspace_item.setObjectName("navActive")
        sidebar_layout.addWidget(workspace_item)

        sidebar_layout.addSpacing(18)
        capture_caption = QLabel("CAPTURE FLOW")
        capture_caption.setObjectName("sideCaption")
        sidebar_layout.addWidget(capture_caption)
        capture_info = QLabel("1   Capture a screen\n\n2   Ask a question\n\n3   Get an answer")
        capture_info.setObjectName("sideInfo")
        sidebar_layout.addWidget(capture_info)
        sidebar_layout.addStretch()

        privacy = QFrame()
        privacy.setObjectName("privacyCard")
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.setContentsMargins(14, 14, 14, 14)
        privacy_layout.setSpacing(5)
        privacy_title = QLabel("Private by default")
        privacy_title.setObjectName("privacyTitle")
        privacy_text = QLabel("Screenshots stay in memory until you close the app.")
        privacy_text.setObjectName("privacyText")
        privacy_text.setWordWrap(True)
        privacy_layout.addWidget(privacy_title)
        privacy_layout.addWidget(privacy_text)
        sidebar_layout.addWidget(privacy)
        shell.addWidget(sidebar)

        body = QWidget()
        body.setObjectName("body")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(34, 28, 34, 24)
        layout.setSpacing(22)

        topbar = QHBoxLayout()
        topbar.setSpacing(12)
        heading = QVBoxLayout()
        heading.setSpacing(2)
        page_title = QLabel("Workspace")
        page_title.setObjectName("pageTitle")
        page_subtitle = QLabel("Understand what is on your screen.")
        page_subtitle.setObjectName("pageSubtitle")
        heading.addWidget(page_title)
        heading.addWidget(page_subtitle)
        topbar.addLayout(heading)
        topbar.addStretch()
        self.status = QLabel("Ready")
        self.status.setObjectName("statusPill")
        topbar.addWidget(self.status, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(topbar)

        workspace = QHBoxLayout()
        workspace.setSpacing(18)

        capture_card = QFrame()
        capture_card.setObjectName("panel")
        capture_layout = QVBoxLayout(capture_card)
        capture_layout.setContentsMargins(18, 18, 18, 18)
        capture_layout.setSpacing(14)

        capture_header = QHBoxLayout()
        capture_title = QVBoxLayout()
        capture_title.setSpacing(3)
        screen_title = QLabel("Current screen")
        screen_title.setObjectName("panelTitle")
        screen_hint = QLabel("The image used for your next question")
        screen_hint.setObjectName("panelHint")
        capture_title.addWidget(screen_title)
        capture_title.addWidget(screen_hint)
        capture_header.addLayout(capture_title)
        capture_header.addStretch()
        self.capture_button = QPushButton("Capture screen")
        self.capture_button.setObjectName("secondaryButton")
        self.capture_button.clicked.connect(self.capture_screen)
        capture_header.addWidget(self.capture_button, 0, Qt.AlignmentFlag.AlignTop)
        capture_layout.addLayout(capture_header)

        self.preview = QLabel("No screen captured yet\n\nUse Capture screen to begin")
        self.preview.setObjectName("preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(340)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        capture_layout.addWidget(self.preview, 1)

        question_row = QHBoxLayout()
        question_row.setSpacing(10)
        self.question = QLineEdit()
        self.question.setPlaceholderText("Ask about this screen...")
        self.question.returnPressed.connect(self.ask_ai)
        self.ask_button = QPushButton("Ask AI")
        self.ask_button.setObjectName("primaryButton")
        self.ask_button.clicked.connect(self.ask_ai)
        question_row.addWidget(self.question, 1)
        question_row.addWidget(self.ask_button)
        capture_layout.addLayout(question_row)

        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(7)
        self.quick_action_buttons = []
        for label, prompt in (
            ("Explain", "Explain what is visible on this screen in simple terms."),
            ("Extract text", "Extract the important visible text from this screen. Preserve exact wording where possible."),
            ("Summarize", "Summarize the important information visible on this screen in a few bullet points."),
            ("Find issue", "Look for errors, warnings, or anything that appears broken. Explain the likely issue and what to do next."),
        ):
            action = QPushButton(label)
            action.setObjectName("quickAction")
            action.clicked.connect(lambda checked=False, text=prompt: self._run_quick_action(text))
            self.quick_action_buttons.append(action)
            quick_actions.addWidget(action)
        capture_layout.addLayout(quick_actions)
        question_help = QLabel("Press Enter to ask  |  Your screenshot is sent only when you ask")
        question_help.setObjectName("fieldHint")
        capture_layout.addWidget(question_help)
        workspace.addWidget(capture_card, 3)

        response_card = QFrame()
        response_card.setObjectName("responseCard")
        response_layout = QVBoxLayout(response_card)
        response_layout.setContentsMargins(20, 18, 20, 18)
        response_layout.setSpacing(12)
        response_header = QHBoxLayout()
        response_title = QVBoxLayout()
        response_title.setSpacing(3)
        response_label = QLabel("Answer")
        response_label.setObjectName("panelTitle")
        response_hint = QLabel("Clear, grounded observations")
        response_hint.setObjectName("panelHint")
        response_title.addWidget(response_label)
        response_title.addWidget(response_hint)
        response_header.addLayout(response_title)
        response_header.addStretch()
        self.response_meta = QLabel(self.settings.model)
        self.response_meta.setObjectName("modelPill")
        response_header.addWidget(self.response_meta, 0, Qt.AlignmentFlag.AlignTop)
        self.copy_button = QPushButton("Copy")
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self._copy_answer)
        response_header.addWidget(self.copy_button, 0, Qt.AlignmentFlag.AlignTop)
        response_layout.addLayout(response_header)
        self.response = QTextBrowser()
        self.response.setOpenExternalLinks(True)
        self.response.setPlaceholderText("Your answer will appear here after you ask a question.")
        self.response.setMinimumWidth(280)
        response_layout.addWidget(self.response, 1)
        workspace.addWidget(response_card, 2)
        layout.addLayout(workspace, 1)

        footer = QLabel("SeeWhatISee  /  Screen understanding assistant")
        footer.setObjectName("footer")
        layout.addWidget(footer)
        shell.addWidget(body, 1)
        self.setCentralWidget(root)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget { background: #0e1117; color: #e8ebf0; font-family: Segoe UI; font-size: 13px; }
            #sidebar { background: #151920; border-right: 1px solid #252b35; }
            #body { background: #0e1117; }
            #brandMark { background: #d5a66a; color: #17130e; border-radius: 7px; font-size: 16px; font-weight: 800; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; qproperty-alignment: AlignCenter; }
            #brandName { color: #f2f0eb; font-size: 15px; font-weight: 700; }
            #sideCaption { color: #77808f; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            #navActive { background: #242a33; color: #f0d2a7; border-radius: 7px; padding: 10px 8px; font-weight: 600; }
            #sideInfo { color: #a0a8b5; padding: 4px 6px; }
            #privacyCard { background: #1b2028; border: 1px solid #2b323d; border-radius: 9px; }
            #privacyTitle { color: #e2c08f; font-weight: 600; }
            #privacyText { color: #858e9d; font-size: 11px; }
            #pageTitle { color: #f4f5f7; font-size: 24px; font-weight: 700; }
            #pageSubtitle { color: #818a99; font-size: 13px; }
            #statusPill { background: #19251f; color: #8cc09d; border: 1px solid #2b4937; border-radius: 13px; padding: 6px 11px; font-size: 12px; }
            #panel, #responseCard { background: #171c24; border: 1px solid #29313c; border-radius: 11px; }
            #panelTitle { color: #f0f2f5; font-size: 15px; font-weight: 650; }
            #panelHint, #fieldHint { color: #7d8796; font-size: 11px; }
            #preview { background: #10141a; border: 1px dashed #3a4350; border-radius: 8px; color: #737e8d; font-size: 13px; }
            QLineEdit { background: #10141a; border: 1px solid #384250; border-radius: 7px; padding: 11px 12px; color: #f1f3f5; selection-background-color: #b48551; }
            QLineEdit:focus { border: 1px solid #c29662; }
            QPushButton { min-height: 38px; padding: 0 15px; border-radius: 7px; color: #e9edf2; font-weight: 600; }
            #secondaryButton { background: #252c36; border: 1px solid #3a4553; }
            #secondaryButton:hover { background: #2e3743; }
            #primaryButton { background: #c18d52; border: 1px solid #d7a66b; color: #17130e; }
            #primaryButton:hover { background: #d29d5d; }
            #quickAction, #copyButton { background: #202731; border: 1px solid #35404e; color: #b8c1ce; min-height: 30px; padding: 0 10px; font-size: 11px; }
            #quickAction:hover, #copyButton:hover { background: #29323e; color: #f0f2f5; }
            QPushButton:disabled { background: #252a32; border-color: #303640; color: #697382; }
            #modelPill { background: #202731; color: #aeb8c6; border: 1px solid #35404e; border-radius: 11px; padding: 5px 9px; font-size: 11px; }
            QTextBrowser { background: #10141a; border: 1px solid #2b333f; border-radius: 7px; color: #dce1e8; padding: 10px; }
            #footer { color: #5f6978; font-size: 11px; }
        """)

    def _setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self._tray_icon(), self)
        self.tray_icon.setToolTip(f"SeeWhatISee - {self.hotkey.shortcut_text} to capture")
        menu = QMenu()
        show_action = QAction("Show SeeWhatISee", self)
        show_action.triggered.connect(self._show_window)
        capture_action = QAction("Capture screen", self)
        capture_action.triggered.connect(self._capture_from_hotkey)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_application)
        menu.addAction(show_action)
        menu.addAction(capture_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()

    @staticmethod
    def _tray_icon() -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.setPen(Qt.GlobalColor.transparent)
        painter.drawRoundedRect(1, 1, 30, 30, 7, 7)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "S")
        painter.end()
        return QIcon(pixmap)

    def capture_screen(self) -> None:
        try:
            self.image = self.capture.capture_primary()
            self.preview.setPixmap(QPixmap.fromImage(self.image).scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.status.setText("Captured")
            self.response.clear()
            self.current_answer = ""
            self.copy_button.setEnabled(False)
        except CaptureError as error:
            self._show_error(str(error))

    def _capture_from_hotkey(self) -> None:
        self.capture_screen()
        self._show_window()
        self.question.setFocus()

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._show_window()

    def _quit_application(self) -> None:
        self._quitting = True
        self.hotkey.unregister()
        self.tray_icon.hide()
        QApplication.quit()

    def _run_quick_action(self, prompt: str) -> None:
        self.question.setText(prompt)
        self.ask_ai()

    def _copy_answer(self) -> None:
        if not self.current_answer:
            return
        QApplication.clipboard().setText(self.current_answer)
        self.status.setText("Copied")

    def ask_ai(self) -> None:
        if self.image is None:
            self._show_error("Capture your screen before asking a question.")
            return
        question = self.question.text().strip()
        if not question:
            self._show_error("Enter a question about the captured screen.")
            return
        if not self.settings.api_key and not self._is_local_ollama():
            key_name = "OLLAMA_API_KEY" if self.settings.provider == "ollama" else "OPENAI_API_KEY"
            self._show_error(f"No API key found. Add {key_name} to your .env file and restart the app.")
            return
        image_bytes = self.capture.to_png_bytes(self.image)
        self.ask_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.status.setText("Analyzing")
        self.response.setText("Thinking...")
        self.copy_button.setEnabled(False)
        for button in self.quick_action_buttons:
            button.setEnabled(False)
        future = self.executor.submit(self._request_answer, image_bytes, question)
        future.add_done_callback(self._handle_future)

    def _request_answer(self, image_bytes: bytes, question: str) -> str:
        try:
            return VisionService(
                self.settings.api_key,
                self.settings.model,
                self.settings.base_url,
            ).answer(image_bytes, question)
        except VisionError as error:
            raise RuntimeError(str(error)) from error

    def _is_local_ollama(self) -> bool:
        return self.settings.provider == "ollama" and (
            self.settings.base_url.startswith("http://localhost")
            or self.settings.base_url.startswith("http://127.0.0.1")
        )

    def _handle_future(self, future) -> None:
        try:
            self.signals.completed.emit(future.result())
        except Exception as error:
            self.signals.failed.emit(str(error))

    def _show_answer(self, answer: str) -> None:
        self.current_answer = answer
        self.response.setMarkdown(answer)
        self.status.setText("Ready")
        self.ask_button.setEnabled(True)
        self.capture_button.setEnabled(True)
        self.copy_button.setEnabled(True)
        for button in self.quick_action_buttons:
            button.setEnabled(True)

    def _show_error(self, message: str) -> None:
        self.current_answer = ""
        self.response.setText(f"<span style='color:#ef9b9b'>{message}</span>")
        self.status.setText("Action needed")
        self.ask_button.setEnabled(True)
        self.capture_button.setEnabled(True)
        self.copy_button.setEnabled(False)
        for button in self.quick_action_buttons:
            button.setEnabled(True)

    def closeEvent(self, event) -> None:
        if not self._quitting:
            self.hide()
            self.status.setText("Running in background")
            event.ignore()
            return
        application = QApplication.instance()
        if application is not None:
            application.removeNativeEventFilter(self.hotkey)
        self.tray_icon.hide()
        self.executor.shutdown(wait=False, cancel_futures=True)
        event.accept()
