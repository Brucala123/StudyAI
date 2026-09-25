import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agents.study_agent import StudyAgent
from models.errors import AgentError


def response(content="", tool_calls=None):
    """Cria uma resposta falsa no formato básico usado pelo Ollama."""
    return SimpleNamespace(
        message=SimpleNamespace(
            content=content,
            tool_calls=tool_calls or [],
        )
    )


def tool_call(name, arguments):
    """Cria uma chamada de ferramenta falsa do Ollama."""
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        )
    )


def test_tool_roundtrip(registry):
    client = Mock()

    client.chat.side_effect = [
        response(
            tool_calls=[
                tool_call(
                    "create_subject",
                    {
                        "name": "Física",
                        "description": "",
                    },
                )
            ]
        ),
        response(content="Matéria cadastrada."),
    ]

    agent = StudyAgent(
        client=client,
        model="test-model",
        prompt="Tutor",
        tools=registry,
    )

    result = agent.respond("Cadastre Física")

    assert result == "Matéria cadastrada."

    subjects = registry.functions["list_subjects"]()

    assert len(subjects) == 1
    assert subjects[0]["name"] == "Física"

    # A segunda chamada ao modelo deve conter
    # o resultado devolvido pela ferramenta.
    second_call_messages = client.chat.call_args_list[1].kwargs["messages"]

    assert any(
        isinstance(item, dict)
        and item.get("role") == "tool"
        for item in second_call_messages
    )

    agent.clear_conversation()

    assert agent.history == []


@pytest.mark.parametrize(
    "name,args",
    [
        ("unknown", "{}"),
        ("create_subject", "[]"),
        ("create_subject", "{"),
        ("create_subject", '{"name": true}'),
        ("list_subjects", '{"surprise": 1}'),
        (
            "create_topic",
            '{"subject_id": 999, "name": "X"}',
        ),
    ],
)
def test_invalid_tool_arguments(registry, name, args):
    result = json.loads(
        registry.execute(name, args)
    )

    assert result["ok"] is False


def test_strict_schemas(registry):
    for schema in registry.schemas:
        params = schema["parameters"]

        assert params["required"] == list(
            params["properties"]
        )

        assert params["additionalProperties"] is False
        assert schema["strict"] is True


def test_connection_error_keeps_successful_tool_history(registry):
    client = Mock()

    client.chat.side_effect = [
        response(
            tool_calls=[
                tool_call(
                    "create_subject",
                    {
                        "name": "Física",
                        "description": "",
                    },
                )
            ]
        ),
        ConnectionError("Ollama indisponível"),
    ]

    agent = StudyAgent(
        client=client,
        model="test-model",
        prompt="Tutor",
        tools=registry,
    )

    with pytest.raises(AgentError):
        agent.respond("Cadastre Física")

    subjects = registry.functions["list_subjects"]()

    assert len(subjects) == 1

    assert agent.history[-1]["role"] == "tool"


def test_round_limit_requests_final_answer(registry):
    client = Mock()

    client.chat.side_effect = [
        response(
            tool_calls=[
                tool_call(
                    "list_subjects",
                    {},
                )
            ]
        ),
        response(
            content="Sem matérias."
        ),
    ]

    agent = StudyAgent(
        client=client,
        model="test-model",
        prompt="Tutor",
        tools=registry,
        max_tool_rounds=1,
    )

    result = agent.respond("Liste")

    assert result == "Sem matérias."

    # Na rodada final as ferramentas são removidas,
    # obrigando o modelo a responder.
    assert (
        client.chat.call_args_list[-1]
        .kwargs["tools"]
        is None
    )


def test_empty_response_raises_agent_error(registry):
    client = Mock()

    client.chat.return_value = response(
        content="",
        tool_calls=[],
    )

    agent = StudyAgent(
        client=client,
        model="test-model",
        prompt="Tutor",
        tools=registry,
    )

    with pytest.raises(AgentError):
        agent.respond("Olá")