class ValidationError(ValueError):
    """Entrada inválida, com mensagem segura para o estudante."""


class NotFoundError(ValidationError):
    """Registro solicitado não existe."""


class AgentError(RuntimeError):
    """Falha de comunicação ou resposta incompleta da IA."""
