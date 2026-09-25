from unittest.mock import Mock
from types import SimpleNamespace

from agents.base_agent import BaseAgent
from agents.tutor_agent import TutorAgent


def test_tutor_agent_inherits_base_agent(registry):
    client = Mock()

    client.chat.return_value = SimpleNamespace(
        message=SimpleNamespace(
            content="Explicação de teste.",
            tool_calls=[],
        )
    )

    agent = TutorAgent(
        client=client,
        model="test-model",
        prompt="Você é um tutor.",
        tools=registry,
    )

    assert isinstance(agent, BaseAgent)

    result = agent.respond(
        "Explique pressão hidrostática."
    )

    assert result == "Explicação de teste."

    client.chat.assert_called_once()
    