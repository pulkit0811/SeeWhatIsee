import os
import unittest
from unittest.mock import patch

from PySide6.QtGui import QImage

from seewhatisee.ai.vision import VisionError, VisionService
from seewhatisee.capture.screen import ScreenCapture
from seewhatisee.config.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_settings_read_environment(self) -> None:
        with patch.dict(os.environ, {"AI_PROVIDER": "openai", "OPENAI_API_KEY": "test-key", "SEEWHATISEE_MODEL": "test-model"}):
            settings = Settings.from_environment()
        self.assertEqual(settings.provider, "openai")
        self.assertEqual(settings.api_key, "test-key")
        self.assertEqual(settings.base_url, "")
        self.assertEqual(settings.model, "test-model")

    def test_settings_use_default_model(self) -> None:
        with patch.object(Settings, "_load_dotenv"), patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_environment()
        self.assertEqual(settings.provider, "ollama")
        self.assertEqual(settings.api_key, "")
        self.assertEqual(settings.base_url, "https://ollama.com/v1")
        self.assertEqual(settings.model, "gemma4")

    def test_settings_read_ollama_environment(self) -> None:
        environment = {
            "AI_PROVIDER": "ollama",
            "OLLAMA_API_KEY": "ollama-key",
            "OLLAMA_BASE_URL": "https://ollama.com/v1",
            "SEEWHATISEE_MODEL": "gemma4",
        }
        with patch.object(Settings, "_load_dotenv"), patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_environment()
        self.assertEqual(settings.provider, "ollama")
        self.assertEqual(settings.api_key, "ollama-key")
        self.assertEqual(settings.base_url, "https://ollama.com/v1")
        self.assertEqual(settings.model, "gemma4")


class VisionTests(unittest.TestCase):
    def test_answer_sends_image_and_question(self) -> None:
        fake_response = type(
            "Response",
            (),
            {"choices": [type("Choice", (), {"message": type("Message", (), {"content": " It is a desktop. "})()})()]},
        )()
        fake_client = type(
            "Client",
            (),
            {"chat": type("Chat", (), {"completions": type("Completions", (), {"create": unittest.mock.Mock(return_value=fake_response)})()})()},
        )()

        with patch("openai.OpenAI", return_value=fake_client):
            service = VisionService("test-key", "test-model")
            answer = service.answer(b"png-bytes", "What is visible?")

        self.assertEqual(answer, "It is a desktop.")
        request = fake_client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "test-model")
        self.assertEqual(request["messages"][1]["content"][0]["text"], "What is visible?")
        self.assertIn("cG5nLWJ5dGVz", request["messages"][1]["content"][1]["image_url"]["url"])

    def test_answer_maps_authentication_errors(self) -> None:
        fake_client = type(
            "Client",
            (),
            {"chat": type("Chat", (), {"completions": type("Completions", (), {"create": unittest.mock.Mock(side_effect=Exception("401 authentication failed"))})()})()},
        )()

        with patch("openai.OpenAI", return_value=fake_client):
            service = VisionService("test-key", "test-model")
            with self.assertRaisesRegex(VisionError, "API key was rejected"):
                service.answer(b"png-bytes", "What is visible?")

    def test_answer_rejects_empty_response(self) -> None:
        fake_response = type("Response", (), {"choices": []})()
        fake_client = type(
            "Client",
            (),
            {"chat": type("Chat", (), {"completions": type("Completions", (), {"create": unittest.mock.Mock(return_value=fake_response)})()})()},
        )()

        with patch("openai.OpenAI", return_value=fake_client):
            service = VisionService("test-key", "test-model")
            with self.assertRaisesRegex(VisionError, "empty response"):
                service.answer(b"png-bytes", "What is visible?")


class CaptureTests(unittest.TestCase):
    def test_png_bytes_are_valid_and_resized(self) -> None:
        image = QImage(3000, 1500, QImage.Format.Format_RGB888)
        image.fill(0)
        encoded = ScreenCapture.to_png_bytes(image, max_dimension=1000)
        decoded = QImage.fromData(encoded, "PNG")
        self.assertEqual((decoded.width(), decoded.height()), (1000, 500))


if __name__ == "__main__":
    unittest.main()
