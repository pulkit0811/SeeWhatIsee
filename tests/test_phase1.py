import os
import unittest
from unittest.mock import patch

from PySide6.QtGui import QImage

from seewhatisee.capture.screen import ScreenCapture
from seewhatisee.config.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_settings_read_environment(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "SEEWHATISEE_MODEL": "test-model"}):
            settings = Settings.from_environment()
        self.assertEqual(settings.api_key, "test-key")
        self.assertEqual(settings.model, "test-model")


class CaptureTests(unittest.TestCase):
    def test_png_bytes_are_valid_and_resized(self) -> None:
        image = QImage(3000, 1500, QImage.Format.Format_RGB888)
        image.fill(0)
        encoded = ScreenCapture.to_png_bytes(image, max_dimension=1000)
        decoded = QImage.fromData(encoded, "PNG")
        self.assertEqual((decoded.width(), decoded.height()), (1000, 500))


if __name__ == "__main__":
    unittest.main()
