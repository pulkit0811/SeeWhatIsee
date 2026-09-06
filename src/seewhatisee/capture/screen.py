from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage


class CaptureError(RuntimeError):
    pass


class ScreenCapture:
    def capture_primary(self) -> QImage:
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                raise RuntimeError("No primary screen is available")
            return screen.grabWindow(0).toImage().convertToFormat(QImage.Format.Format_RGB888)
        except Exception as error:
            raise CaptureError("The screen could not be captured. Check display permissions and try again.") from error

    @staticmethod
    def to_png_bytes(image: QImage, max_dimension: int = 1920) -> bytes:
        if max(image.width(), image.height()) > max_dimension:
            prepared = image.scaled(max_dimension, max_dimension, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            prepared = image
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        prepared.save(buffer, "PNG")
        return bytes(buffer.data())
