from dataclasses import asdict
from database.repositories import Repository
from models.validation import positive_id, text


class SubjectTools:
    def __init__(self, repository: Repository):
        self.repository = repository

    def list_subjects(self) -> list[dict]:
        """Lista matérias cadastradas com seus identificadores."""
        return [asdict(item) for item in self.repository.list_subjects()]

    def create_subject(self, name: str, description: str = "") -> dict:
        """Cadastra uma matéria solicitada pelo estudante."""
        return asdict(self.repository.create_subject(text(name, "Nome"), text(description, "Descrição", required=False)))

    def list_topics(self, subject_id: int | None = None) -> list[dict]:
        """Lista tópicos de uma matéria; null lista todos."""
        if subject_id is not None:
            self.repository.require_subject(positive_id(subject_id))
        return [asdict(item) for item in self.repository.list_topics(subject_id)]

    def create_topic(self, subject_id: int, name: str, description: str = "") -> dict:
        """Cadastra um tópico em uma matéria existente."""
        self.repository.require_subject(positive_id(subject_id))
        return asdict(self.repository.create_topic(subject_id, text(name, "Nome"), text(description, "Descrição", required=False)))
