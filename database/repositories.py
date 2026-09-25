"""SQL parametrizado e persistência; regras de domínio ficam nos serviços."""
import sqlite3
from pathlib import Path
from typing import Any
from models.entities import Subject, Topic
from models.errors import NotFoundError
from database.connection import connect


class Repository:
    def __init__(self, path: Path):
        self.path = path

    def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with connect(self.path) as connection:
            return [dict(row) for row in connection.execute(sql, params)]

    def insert(self, sql: str, params: tuple) -> int:
        with connect(self.path) as connection:
            return int(connection.execute(sql, params).lastrowid)

    def require_subject(self, subject_id: int) -> Subject:
        rows = self.query("SELECT * FROM subjects WHERE id = ?", (subject_id,))
        if not rows:
            raise NotFoundError("Matéria não encontrada.")
        return Subject(**rows[0])

    def require_topic(self, topic_id: int) -> Topic:
        rows = self.query("SELECT * FROM topics WHERE id = ?", (topic_id,))
        if not rows:
            raise NotFoundError("Tópico não encontrado.")
        return Topic(**rows[0])

    def require_exercise(self, exercise_id: int) -> dict:
        rows = self.query("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
        if not rows:
            raise NotFoundError("Exercício não encontrado.")
        return rows[0]

    def list_subjects(self) -> list[Subject]:
        return [Subject(**row) for row in self.query("SELECT * FROM subjects ORDER BY name")]

    def create_subject(self, name: str, description: str) -> Subject:
        key = self.insert("INSERT INTO subjects(name, description) VALUES (?, ?)", (name, description))
        return self.require_subject(key)

    def list_topics(self, subject_id: int | None = None) -> list[Topic]:
        rows = self.query(
            "SELECT * FROM topics WHERE (? IS NULL OR subject_id = ?) ORDER BY name",
            (subject_id, subject_id),
        )
        return [Topic(**row) for row in rows]

    def create_topic(self, subject_id: int, name: str, description: str) -> Topic:
        key = self.insert(
            "INSERT INTO topics(subject_id, name, description) VALUES (?, ?, ?)",
            (subject_id, name, description),
        )
        return self.require_topic(key)

    def attempt_counts(self, topic_id: int, connection: sqlite3.Connection | None = None) -> tuple[int, int]:
        sql = """SELECT COUNT(*) AS total, COALESCE(SUM(a.is_correct), 0) AS correct
                 FROM attempts a JOIN exercises e ON a.exercise_id = e.id WHERE e.topic_id = ?"""
        if connection is not None:
            row = connection.execute(sql, (topic_id,)).fetchone()
        else:
            row = self.query(sql, (topic_id,))[0]
        return row["total"], row["correct"]
