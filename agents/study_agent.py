"""Loop de tool calling usando Ollama local."""

import json
from datetime import datetime
from typing import Any

from ollama import Client, ResponseError

from models.errors import AgentError
from tools.registry import ToolRegistry


class StudyAgent:
    def __init__(
        self,
        client: Client,
        model: str,
        prompt: str,
        tools: ToolRegistry,
        max_tool_rounds: int = 8,
    ):
        self.client = client
        self.model = model
        self.prompt = prompt
        self.tools = tools
        self.max_tool_rounds = max_tool_rounds
        self.history: list[Any] = []

    def clear_conversation(self) -> None:
        self.history.clear()

    def _ollama_tools(self) -> list[dict]:
        """
        Converte os schemas atuais do ToolRegistry
        para o formato esperado pelo Ollama.
        """
        converted_tools = []

        for schema in self.tools.schemas:
            converted_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": schema["name"],
                        "description": schema["description"] or "",
                        "parameters": schema["parameters"],
                    },
                }
            )

        return converted_tools

    def respond(self, message: str) -> str:
        self.history.append(
            {
                "role": "user",
                "content": message,
            }
        )

        try:
            for round_index in range(self.max_tool_rounds + 1):

                system_message = {
                    "role": "system",
                    "content": (
                        self.prompt
                        + "\n\nData/hora local: "
                        + datetime.now().astimezone().isoformat()
                    ),
                }

                messages = [
                    system_message,
                    *self.history,
                ]

                # Na última rodada não oferecemos ferramentas,
                # obrigando o modelo a produzir uma resposta final.
                available_tools = (
                    None
                    if round_index == self.max_tool_rounds
                    else self._ollama_tools()
                )

                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    tools=available_tools,
                    think=False,
                    options={
                        "temperature": 0.2,
                    },
                )

                assistant_message = response.message

                # Guarda a resposta do modelo no histórico.
                self.history.append(assistant_message)

                tool_calls = assistant_message.tool_calls or []

                # Se não chamou nenhuma ferramenta,
                # temos a resposta final.
                if not tool_calls:
                    content = assistant_message.content

                    if not content:
                        raise AgentError(
                            "O modelo local retornou uma resposta vazia."
                        )

                    return content

                # Executa todas as ferramentas solicitadas.
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    arguments = tool_call.function.arguments or {}

                    arguments_json = json.dumps(
                        arguments,
                        ensure_ascii=False,
                    )

                    result = self.tools.execute(
                        function_name,
                        arguments_json,
                    )

                    # O resultado da ferramenta volta para o modelo.
                    self.history.append(
                        {
                            "role": "tool",
                            "tool_name": function_name,
                            "content": result,
                        }
                    )

            raise AgentError(
                "Limite de chamadas de ferramentas atingido."
            )

        except ConnectionError:
            raise AgentError(
                "Não foi possível conectar ao Ollama. "
                "Verifique se o serviço está funcionando."
            ) from None

        except ResponseError as error:
            status = getattr(error, "status_code", None)

            if status == 404:
                raise AgentError(
                    f"O modelo '{self.model}' não foi encontrado no Ollama."
                ) from None

            raise AgentError(
                "O Ollama recusou a solicitação do modelo."
            ) from None                                                                                                                                                                                                                                                                                                                                                                             