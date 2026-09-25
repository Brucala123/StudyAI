"""Configuração independente do diretório em que o terminal foi aberto."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    model: str = "qwen3:1.7b"
    ollama_host: str = "http://127.0.0.1:11434"
    database_path: Path = ROOT / "data" / "study.db"
    prompt_path: Path = ROOT / "prompts" / "study_agent_prompt.txt"

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(ROOT / ".env")

        return cls(
            model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b").strip()
            or "qwen3:1.7b",
            ollama_host=os.getenv(
                "OLLAMA_HOST",
                "http://127.0.0.1:11434",
            ).strip()
            or "http://127.0.0.1:11434",
        )