"""Estratégia inicial: todas as tentativas têm o mesmo peso."""
from dataclasses import asdict
import math
from database.connection import connect
from database.repositories import Repository
from models.entities import TopicPerformance
from models.errors import ValidationError
from models.validation import positive_id, text, limit_value


def calculate_mastery(correct: int, attempts: int) -> float:
    if type(correct) is not int or type(attempts) is not int or not 0 <= correct <= attempts:
        raise ValidationError("Contagens de acertos e tentativas inválidas.")
    return round(correct / attempts * 100, 2) if attempts else 0.0


class PerformanceService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def get_topic_performance(self, topic_id: int) -> TopicPerformance:
        topic = self.repository.require_topic(positive_id(topic_id))
        total, correct = self.repository.attempt_counts(topic_id)
        return TopicPerformance(topic.id, topic.name, topic.subject_id, total, correct,
                                calculate_mastery(correct, total), total > 0)

    def get_weak_topics(self, threshold: float = 60, limit: int = 10) -> dict:
        if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 100:
            raise ValidationError("O limiar deve estar entre 0 e 100.")
        limit_value(limit)
        measured, unassessed = [], []
        for topic in self.repository.list_topics():
            performance = self.get_topic_performance(topic.id)
            if not performance.has_evidence:
                unassessed.append(asdict(performance))
            elif performance.mastery_level < threshold:
                measured.append(asdict(performance))
        measured.sort(key=lambda item: (item["mastery_level"], -item["attempts"], item["topic_id"]))
        return {"weak_topics": measured[:limit], "unassessed_topics": unassessed[:limit]}

    def register_attempt(self, exercise_id: int, student_answer: str, is_correct: bool,
                         error_type: str = "", feedback: str = "") -> dict:
        exercise = self.repository.require_exercise(positive_id(exercise_id))
        if type(is_correct) is not bool:
            raise ValidationError("O resultado deve ser true ou false.")
        answer = text(student_answer, "Resposta")
        error = text(error_type, "Tipo de erro", required=False)
        feedback = text(feedback, "Feedback", required=False)
        # Tentativa e domínio são gravados na mesma transação.
        with connect(self.repository.path) as connection:
            cursor = connection.execute(
                """INSERT INTO attempts(exercise_id, student_answer, is_correct, error_type, feedback)
                   VALUES (?, ?, ?, ?, ?)""", (exercise_id, answer, int(is_correct), error, feedback))
            total, correct = self.repository.attempt_counts(exercise["topic_id"], connection)
            mastery = calculate_mastery(correct, total)
            connection.execute(
                """UPDATE topics SET mastery_level = ?,
                   updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?""",
                (mastery, exercise["topic_id"]))
            return {"attempt_id": cursor.lastrowid, "topic_id": exercise["topic_id"],
                    "attempts": total, "correct": correct, "mastery_level": mastery}
