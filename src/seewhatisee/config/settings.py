import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str

    @classmethod
    def from_environment(cls) -> "Settings":
        cls._load_dotenv()
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            model=os.getenv("SEEWHATISEE_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
        )

    @staticmethod
    def _load_dotenv() -> None:
        env_file = Path.cwd() / ".env"
        if not env_file.is_file():
            return
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip().strip('"').strip("'")
