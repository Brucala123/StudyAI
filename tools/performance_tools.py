from dataclasses import asdict
from services.performance_service import PerformanceService


class PerformanceTools:
    def __init__(self, performance: PerformanceService):
        self.performance = performance

    def get_topic_performance(self, topic_id: int) -> dict:
        """Consulta acertos, tentativas e domínio de um tópico."""
        return asdict(self.performance.get_topic_performance(topic_id))

    def get_weak_topics(self, threshold: float = 60, limit: int = 10) -> dict:
        """Busca tópicos abaixo do limiar e separa tópicos ainda não avaliados."""
        return self.performance.get_weak_topics(threshold, limit)

    def register_attempt(self, exercise_id: int, student_answer: str, is_correct: bool,
                         error_type: str = "", feedback: str = "") -> dict:
        """Registra uma tentativa real com avaliação fundamentada e atualiza domínio."""
        return self.performance.register_attempt(exercise_id, student_answer, is_correct, error_type, feedback)
