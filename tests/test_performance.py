import pytest
from models.errors import ValidationError
from services.performance_service import calculate_mastery, PerformanceService
from tools.subject_tools import SubjectTools
from tools.study_tools import StudyTools


@pytest.mark.parametrize("correct,total,expected", [(7,10,70), (0,0,0), (1,3,33.33), (4,4,100)])
def test_mastery(correct, total, expected):
    assert calculate_mastery(correct, total) == expected


@pytest.mark.parametrize("correct,total", [(2,1), (-1,2), (0,-1), (True,2)])
def test_invalid_counts(correct, total):
    with pytest.raises(ValidationError):
        calculate_mastery(correct, total)


def test_attempts_update_mastery_atomically(repository, topic):
    study = StudyTools(repository)
    exercise = study.create_exercise(topic["id"], "Quanto é 1+1?", "easy")
    service = PerformanceService(repository)
    for index in range(10):
        service.register_attempt(exercise["exercise_id"], "2", index < 7)
    performance = service.get_topic_performance(topic["id"])
    assert (performance.attempts, performance.correct, performance.mastery_level) == (10, 7, 70)
    assert repository.require_topic(topic["id"]).mastery_level == 70
    assert len(study.list_attempts(topic["id"])) == 10
    with pytest.raises(ValidationError):
        service.register_attempt(exercise["exercise_id"], "2", "false")
    assert service.get_topic_performance(topic["id"]).attempts == 10


def test_weak_topics_exclude_unassessed(repository, topic):
    subject_tools = SubjectTools(repository)
    unseen = subject_tools.create_topic(topic["subject_id"], "Torção")
    study = StudyTools(repository)
    exercise = study.create_exercise(topic["id"], "Questão", "medium")
    service = PerformanceService(repository)
    service.register_attempt(exercise["exercise_id"], "Resposta", False, "conceitual", "Revisar.")
    results = service.get_weak_topics()
    assert [row["topic_id"] for row in results["weak_topics"]] == [topic["id"]]
    assert [row["topic_id"] for row in results["unassessed_topics"]] == [unseen["id"]]
