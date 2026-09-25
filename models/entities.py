"""Entidades centrais; datas são strings ISO 8601 nos limites do SQLite."""
from dataclasses import dataclass
from enum import StrEnum


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class Subject:
    id: int
    name: str
    description: str
    created_at: str


@dataclass(frozen=True)
class Topic:
    id: int
    subject_id: int
    name: str
    description: str
    mastery_level: float
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TopicPerformance:
    topic_id: int
    topic_name: str
    subject_id: int
    attempts: int
    correct: int
    mastery_level: float
    has_evidence: bool
