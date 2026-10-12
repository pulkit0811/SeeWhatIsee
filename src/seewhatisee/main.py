import sys

from PySide6.QtWidgets import QApplication

from seewhatisee.ui.window import MainWindow


def main() -> None:
    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(False)
    application.setApplicationName("SeeWhatISee")
    application.setOrganizationName("SeeWhatISee")
    window = MainWindow()
    window.show()
    sys.exit(application.exec())

