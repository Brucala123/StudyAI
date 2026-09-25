"""Agente principal e roteador inicial do StudyAI."""

import logging

from agents.base_agent import BaseAgent
from agents.tutor_agent import TutorAgent


logger = logging.getLogger(__name__)


class StudyAgent(BaseAgent):
    """
    Agente principal do StudyAI.

    Decide se uma mensagem deve ser tratada diretamente
    ou delegada ao TutorAgent.
    """

    def __init__(
        self,
        *args,
        tutor_agent: TutorAgent | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.tutor_agent = tutor_agent

    def clear_conversation(self) -> None:
        """Limpa a memória do agente principal e dos especialistas."""
        super().clear_conversation()

        if self.tutor_agent is not None:
            self.tutor_agent.clear_conversation()

    def _route_message(self, message: str) -> str:
        """
        Usa o próprio modelo local para decidir
        se a mensagem deve ir para o TutorAgent.
        """

        routing_prompt = """
Você é o roteador do StudyAI.

Classifique a mensagem do estudante em apenas UMA categoria:

TUTOR
Use quando o estudante estiver pedindo:
- explicação de conteúdo;
- ajuda para entender um conceito;
- resolução explicada de exercício;
- esclarecimento de dúvida acadêmica;
- demonstração passo a passo;
- ajuda com fórmulas ou cálculos.

GENERAL
Use para:
- cadastrar matéria;
- cadastrar tópico;
- listar matérias;
- consultar registros;
- salvar informações;
- registrar estudo;
- consultar provas;
- operações administrativas no sistema.

Exemplos:

"Explique pressão hidrostática."
TUTOR

"Não entendi a equação de Bernoulli."
TUTOR

"Resolva esta integral passo a passo."
TUTOR

"Cadastre Física."
GENERAL

"Quais matérias eu tenho?"
GENERAL

"Registre que estudei Física por 40 minutos."
GENERAL

Responda SOMENTE:
TUTOR
ou
GENERAL
"""

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": routing_prompt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            think=False,
            options={
                "temperature": 0,
            },
        )

        decision = (
            response.message.content
            or ""
        ).strip().upper()

        if "TUTOR" in decision and "GENERAL" not in decision:
            return "TUTOR"

        return "GENERAL"

    def respond(self, message: str) -> str:
        """
        Roteia mensagens educacionais para o TutorAgent.
        As demais continuam sendo tratadas pelo agente principal.
        """

        if self.tutor_agent is None:
            return super().respond(message)

        route = self._route_message(message)

        logger.info(
            "StudyAgent route selected: %s",
            route,
        )

        if route == "TUTOR":
            return self.tutor_agent.respond(message)

        return super().respond(message)