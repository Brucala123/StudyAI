"""Ponto de composição: conecta as camadas e inicia o terminal."""

import sqlite3

from ollama import Client, ResponseError
from agents.tutor_agent import TutorAgent
from agents.study_agent import StudyAgent
from cli import run_cli
from config.settings import ROOT, Settings
from config.logging_config import configure_logging
from database.schema import initialize_database
from database.repositories import Repository
from services.performance_service import PerformanceService
from tools.subject_tools import SubjectTools
from tools.study_tools import StudyTools
from tools.performance_tools import PerformanceTools
from tools.registry import ToolRegistry


def main() -> int:
    print("=" * 36)
    print("             StudyAI")
    print("=" * 36)

    client = None

    try:
        settings = Settings.load()

        configure_logging(ROOT)

        initialize_database(
            settings.database_path
        )

        repository = Repository(
            settings.database_path
        )

        registry = ToolRegistry(
            SubjectTools(repository),
            StudyTools(repository),
            PerformanceTools(
                PerformanceService(repository)
            ),
        )

        client = Client(
            host=settings.ollama_host,
            timeout=120.0,
        )

        # Verifica se o Ollama está acessível
        # e se o modelo realmente existe.
        try:
            client.show(settings.model)

        except ConnectionError:
            print(
                "Não foi possível conectar ao Ollama."
            )
            print(
                "Verifique se o serviço está em execução."
            )
            return 1

        except ResponseError:
            print(
                f"O modelo '{settings.model}' "
                "não foi encontrado."
            )
            print(
                f"Execute: ollama pull {settings.model}"
            )
            return 1

        prompt = settings.prompt_path.read_text(
            encoding="utf-8"
        )

        tutor_prompt = (
            ROOT
            / "prompts"
            / "tutor_agent_prompt.txt"
        ).read_text(
            encoding="utf-8"
        )

        tutor_agent = TutorAgent(
            client=client,
            model=settings.model,
            prompt=tutor_prompt,
            tools=registry,
        )

        agent = StudyAgent(
            client=client,
            model=settings.model,
            prompt=prompt,
            tools=registry,
            tutor_agent=tutor_agent,
        )

        run_cli(agent)

        return 0

    except (sqlite3.Error, OSError):
        print(
            "Não foi possível abrir os arquivos "
            "do projeto ou o banco."
        )
        return 1

    except Exception:
        print(
            "Não foi possível iniciar o StudyAI. "
            "Confira a instalação e configuração."
        )
        return 1

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())