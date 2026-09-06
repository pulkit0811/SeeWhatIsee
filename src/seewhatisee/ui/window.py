from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from seewhatisee.ai import VisionError, VisionService
from seewhatisee.capture import CaptureError, ScreenCapture
from seewhatisee.config import Settings


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
        self.setWindowTitle("SeeWhatISee")
        self.setMinimumSize(980, 700)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(18)

        header = QVBoxLayout()
        eyebrow = QLabel("SCREEN UNDERSTANDING ASSISTANT")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("SeeWhatISee")
        title.setObjectName("title")
        subtitle = QLabel("Capture your screen. Ask a question. Get clarity.")
        subtitle.setObjectName("subtitle")
        header.addWidget(eyebrow)
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        content = QFrame()
        content.setObjectName("card")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(22, 22, 22, 22)
        content_layout.setSpacing(14)

        preview_label = QLabel("SCREEN PREVIEW")
        preview_label.setObjectName("sectionLabel")
        self.preview = QLabel("Your captured screen will appear here")
        self.preview.setObjectName("preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(310)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(preview_label)
        content_layout.addWidget(self.preview)

        controls = QVBoxLayout()
        controls.setSpacing(10)
        self.question = QLineEdit()
        self.question.setPlaceholderText("Ask anything about what you see…")
        self.question.returnPressed.connect(self.ask_ai)
        buttons = QVBoxLayout()
        buttons.setSpacing(10)
        self.capture_button = QPushButton("Capture screen")
        self.capture_button.clicked.connect(self.capture_screen)
        self.ask_button = QPushButton("Ask AI")
        self.ask_button.setObjectName("primaryButton")
        self.ask_button.clicked.connect(self.ask_ai)
        buttons.addWidget(self.capture_button)
        buttons.addWidget(self.ask_button)
        controls.addWidget(self.question)
        controls.addLayout(buttons)
        content_layout.addLayout(controls)
        layout.addWidget(content, 3)

        response_card = QFrame()
        response_card.setObjectName("responseCard")
        response_layout = QVBoxLayout(response_card)
        response_layout.setContentsMargins(22, 18, 22, 18)
        response_label = QLabel("AI RESPONSE")
        response_label.setObjectName("sectionLabel")
        self.response = QTextBrowser()
        self.response.setOpenExternalLinks(True)
        self.response.setPlaceholderText("Your answer will appear here after you ask a question.")
        self.response.setMinimumHeight(120)
        response_layout.addWidget(response_label)
        response_layout.addWidget(self.response)
        layout.addWidget(response_card, 2)

        self.status = QLabel("Ready · Screenshots stay in memory until you close the app")
        self.status.setObjectName("status")
        layout.addWidget(self.status)
        self.setCentralWidget(root)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget { background: #10131a; color: #eef2f8; font-family: Segoe UI; font-size: 14px; }
            #eyebrow, #sectionLabel { color: #7e8ba5; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            #title { color: #f7f9fc; font-size: 34px; font-weight: 700; }
            #subtitle { color: #9ba7bb; font-size: 16px; }
            #card, #responseCard { background: #181d27; border: 1px solid #293242; border-radius: 16px; }
            #preview { background: #11151d; border: 1px dashed #3b465a; border-radius: 12px; color: #69778d; }
            QLineEdit { background: #11151d; border: 1px solid #344056; border-radius: 10px; padding: 13px 14px; color: #f7f9fc; }
            QLineEdit:focus { border: 1px solid #7c8cff; }
            QPushButton { background: #252d3b; border: 1px solid #39465d; border-radius: 10px; padding: 12px; color: #eef2f8; font-weight: 600; }
            QPushButton:hover { background: #303b50; }
            QPushButton:disabled { color: #66738a; }
            #primaryButton { background: #6675f5; border: none; }
            #primaryButton:hover { background: #7785ff; }
            QTextBrowser { background: transparent; border: none; color: #dfe6f2; padding: 2px; }
            #status { color: #8592a7; font-size: 12px; }
        """)

    def capture_screen(self) -> None:
        try:
            self.image = self.capture.capture_primary()
            self.preview.setPixmap(QPixmap.fromImage(self.image).scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.status.setText("Ready · Screen captured securely in memory")
            self.response.clear()
        except CaptureError as error:
            self._show_error(str(error))

    def ask_ai(self) -> None:
        if self.image is None:
            self._show_error("Capture your screen before asking a question.")
            return
        question = self.question.text().strip()
        if not question:
            self._show_error("Enter a question about the captured screen.")
            return
        if not self.settings.api_key:
            self._show_error("No API key found. Add OPENAI_API_KEY to your .env file and restart the app.")
            return
        image_bytes = self.capture.to_png_bytes(self.image)
        self.ask_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.status.setText("Analyzing screen · Please wait…")
        self.response.setText("Thinking…")
        future = self.executor.submit(self._request_answer, image_bytes, question)
        future.add_done_callback(self._handle_future)

    def _request_answer(self, image_bytes: bytes, question: str) -> str:
        try:
            return VisionService(self.settings.api_key, self.settings.model).answer(image_bytes, question)
        except VisionError as error:
            raise RuntimeError(str(error)) from error

    def _handle_future(self, future) -> None:
        try:
            self.signals.completed.emit(future.result())
        except Exception as error:
            self.signals.failed.emit(str(error))

    def _show_answer(self, answer: str) -> None:
        self.response.setText(answer)
        self.status.setText("Ready · Analysis complete")
        self.ask_button.setEnabled(True)
        self.capture_button.setEnabled(True)

    def _show_error(self, message: str) -> None:
        self.response.setText(f"<span style='color:#ff9b9b'>{message}</span>")
        self.status.setText("Action needed · Check the message above")
        self.ask_button.setEnabled(True)
        self.capture_button.setEnabled(True)

    def closeEvent(self, event) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
        event.accept()
