from unittest.mock import Mock

import main

from config.settings import Settings


def test_startup_without_ollama_creates_database(
    tmp_path,
    monkeypatch,
    capsys,
):
    database_path = (
        tmp_path
        / "data"
        / "study.db"
    )

    prompt_path = (
        tmp_path
        / "prompt.txt"
    )

    settings = Settings(
        model="qwen3:1.7b",
        ollama_host="http://127.0.0.1:11434",
        database_path=database_path,
        prompt_path=prompt_path,
    )

    monkeypatch.setattr(
        main.Settings,
        "load",
        lambda: settings,
    )

    monkeypatch.setattr(
        main,
        "configure_logging",
        lambda root: None,
    )

    fake_client = Mock()

    fake_client.show.side_effect = ConnectionError(
        "Ollama indisponível"
    )

    monkeypatch.setattr(
        main,
        "Client",
        lambda **kwargs: fake_client,
    )

    assert main.main() == 1

    assert database_path.exists()

    output = capsys.readouterr().out

    assert (
        "Não foi possível conectar ao Ollama"
        in output
    )


def test_cli_exits_without_model_call(
    monkeypatch,
    capsys,
):
    from cli import run_cli

    agent = Mock()

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "sair",
    )

    run_cli(agent)

    agent.respond.assert_not_called()

    assert (
        "próxima"
        in capsys.readouterr().out
    )