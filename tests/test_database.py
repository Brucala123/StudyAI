import sqlite3
import pytest
from database.schema import initialize_database
from database.repositories import Repository
from database.connection import connect
from models.errors import ValidationError, NotFoundError
from tools.subject_tools import SubjectTools
from tools.study_tools import StudyTools


def test_database_creation_is_idempotent(repository):
    initialize_database(repository.path)
    tables = repository.query("SELECT name FROM sqlite_master WHERE type='table'")
    assert {row["name"] for row in tables} == {
        "subjects", "topics", "study_sessions", "exercises", "attempts", "exams", "study_notes"}
    with connect(repository.path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_subject_topic_and_persistence(repository, topic):
    reopened = Repository(repository.path)
    assert reopened.require_topic(topic["id"]).subject_id == topic["subject_id"]
    assert reopened.require_subject(topic["subject_id"]).name == "Análise Vetorial"


def test_subject_sql_input_is_data(repository):
    tools = SubjectTools(repository)
    name = "Física'); DROP TABLE subjects;--"
    assert tools.create_subject(name)["name"] == name
    assert len(tools.list_subjects()) == 1


def test_missing_subject(repository):
    with pytest.raises(NotFoundError):
        SubjectTools(repository).create_topic(999, "Inexistente")


def test_constraints(repository, topic):
    with pytest.raises(sqlite3.IntegrityError):
        repository.insert("INSERT INTO topics(subject_id, name) VALUES (?, ?)", (999, "Órfão"))
    with pytest.raises(sqlite3.IntegrityError):
        SubjectTools(repository).create_topic(topic["subject_id"], topic["name"])


def test_session_relationship_and_duration(repository, topic):
    study = StudyTools(repository)
    other = SubjectTools(repository).create_subject("Física")
    with pytest.raises(ValidationError):
        study.register_study_session(other["id"], 30, topic["id"])
    with pytest.raises(ValidationError):
        study.register_study_session(topic["subject_id"], -1)
    study.register_study_session(topic["subject_id"], 30, topic["id"])
    assert study.list_recent_study_sessions()[0]["topic_name"] == "Curvatura"


def test_notes_exams_exercises(repository, topic):
    study = StudyTools(repository)
    study.save_study_note(topic["id"], "Revisar derivadas.")
    assert study.get_study_notes(topic["id"])[0]["content"] == "Revisar derivadas."
    study.create_exam(topic["subject_id"], "Final", "2099-12-01")
    study.create_exam(topic["subject_id"], "Antiga", "2000-01-01")
    assert [row["title"] for row in study.list_upcoming_exams()] == ["Final"]
    study.create_exercise(topic["id"], "Calcule a curvatura.", "hard")
    assert study.list_exercises(topic["id"])[0]["difficulty"] == "hard"
    with pytest.raises(ValidationError):
        study.create_exam(topic["subject_id"], "Data inválida", "2026-02-30")
    with pytest.raises(ValidationError):
        study.create_exercise(topic["id"], "Questão", "unknown")


@pytest.mark.parametrize("name", ["", "  ", 123, None])
def test_invalid_subject_name(repository, name):
    with pytest.raises(ValidationError):
        SubjectTools(repository).create_subject(name)
