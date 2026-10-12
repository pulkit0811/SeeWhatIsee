import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    provider: str
    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_environment(cls) -> "Settings":
        cls._load_dotenv()
        provider = os.getenv("AI_PROVIDER", "ollama").strip().lower() or "ollama"
        if provider == "ollama":
            api_key = os.getenv("OLLAMA_API_KEY", "").strip()
            base_url = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1").strip()
            model = os.getenv("SEEWHATISEE_MODEL", "gemma4").strip() or "gemma4"
        else:
            provider = "openai"
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            base_url = os.getenv("OPENAI_BASE_URL", "").strip()
            model = os.getenv("SEEWHATISEE_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        return cls(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

    @staticmethod
    def _load_dotenv() -> None:
        env_file = Path.cwd() / ".env"
        if not env_file.is_file():
            return
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            key, separator, value = line.partition("=")
            key = key.strip()
            if separator and key and key not in os.environ:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                    value = value[1:-1]
                os.environ[key] = value
