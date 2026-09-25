from types import SimpleNamespace
from unittest.mock import Mock

from agents.study_agent import StudyAgent


def response(content):
    return SimpleNamespace(
        message=SimpleNamespace(
            content=content,
            tool_calls=[],
        )
    )


def test_study_agent_delegates_to_tutor(registry):
    client = Mock()

    client.chat.return_value = response("TUTOR")

    tutor = Mock()
    tutor.respond.return_value = (
        "Pressão hidrostática é..."
    )

    agent = StudyAgent(
        client=client,
        model="test-model",
        prompt="Agente principal",
        tools=registry,
        tutor_agent=tutor,
    )

    result = agent.respond(
        "Explique pressão hidrostática."
    )

    assert result == "Pressão hidrostática é..."

    tutor.respond.assert_called_once_with(
        "Explique pressão hidrostática."
    )


def test_study_agent_handles_general_request(registry):
    client = Mock()

    client.chat.side_effect = [
        response("GENERAL"),
        response("Aqui estão suas matérias."),
    ]

    tutor = Mock()

    agent = StudyAgent(
        client=client,
        model="test-model",
        prompt="Agente principal",
        tools=registry,
        tutor_agent=tutor,
    )

    result = agent.respond(
        "Quais matérias eu tenho?"
    )

    assert result == "Aqui estão suas matérias."

    tutor.respond.assert_not_called()


def test_clear_conversation_clears_tutor(registry):
    client = Mock()
    tutor = Mock()

    agent = StudyAgent(
        client=client,
        model="test-model",
        prompt="Agente principal",
        tools=registry,
        tutor_agent=tutor,
    )

    agent.history.append(
        {
            "role": "user",
            "content": "teste",
        }
    )

    agent.clear_conversation()

    assert agent.history == []

    tutor.clear_conversation.assert_called_once()