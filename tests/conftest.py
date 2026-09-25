import pytest
from database.repositories import Repository
from database.schema import initialize_database
from tools.subject_tools import SubjectTools
from tools.study_tools import StudyTools
from tools.performance_tools import PerformanceTools
from tools.registry import ToolRegistry
from services.performance_service import PerformanceService


@pytest.fixture
def repository(tmp_path):
    path = tmp_path / "data" / "test.db"
    initialize_database(path)
    return Repository(path)


@pytest.fixture
def registry(repository):
    return ToolRegistry(SubjectTools(repository), StudyTools(repository),
                        PerformanceTools(PerformanceService(repository)))


@pytest.fixture
def topic(repository):
    subjects = SubjectTools(repository)
    subject = subjects.create_subject("Análise Vetorial")
    return subjects.create_topic(subject["id"], "Curvatura")
