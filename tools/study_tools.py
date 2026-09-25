from datetime import date
from database.repositories import Repository
from models.entities import Difficulty
from models.errors import ValidationError
from models.validation import positive_id, text, iso_date, iso_timestamp, limit_value


class StudyTools:
    def __init__(self, repository: Repository):
        self.repository = repository

    def register_study_session(self, subject_id: int, duration_minutes: int,
                               topic_id: int | None = None, started_at: str | None = None,
                               notes: str = "") -> dict:
        """Registra estudo realizado; started_at é ISO com fuso ou null para agora."""
        self.repository.require_subject(positive_id(subject_id))
        if type(duration_minutes) is not int or not 1 <= duration_minutes <= 1440:
            raise ValidationError("A duração deve ser de 1 a 1440 minutos.")
        if topic_id is not None:
            topic = self.repository.require_topic(positive_id(topic_id))
            if topic.subject_id != subject_id:
                raise ValidationError("O tópico não pertence à matéria informada.")
        key = self.repository.insert(
            """INSERT INTO study_sessions(subject_id, topic_id, started_at, duration_minutes, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (subject_id, topic_id, iso_timestamp(started_at), duration_minutes, text(notes, "Notas", required=False)))
        return {"session_id": key}

    def list_recent_study_sessions(self, limit: int = 10) -> list[dict]:
        """Lista sessões recentes, com matéria e tópico."""
        return self.repository.query(
            """SELECT s.*, subjects.name AS subject_name, topics.name AS topic_name
               FROM study_sessions s JOIN subjects ON subjects.id = s.subject_id
               LEFT JOIN topics ON topics.id = s.topic_id ORDER BY s.started_at DESC, s.id DESC LIMIT ?""",
            (limit_value(limit),))

    def create_exam(self, subject_id: int, title: str, exam_date: str, description: str = "") -> dict:
        """Cadastra prova; exam_date deve usar AAAA-MM-DD."""
        self.repository.require_subject(positive_id(subject_id))
        key = self.repository.insert(
            "INSERT INTO exams(subject_id, title, exam_date, description) VALUES (?, ?, ?, ?)",
            (subject_id, text(title, "Título"), iso_date(exam_date), text(description, "Descrição", required=False)))
        return {"exam_id": key}

    def list_upcoming_exams(self, limit: int = 10) -> list[dict]:
        """Lista provas a partir de hoje, inclusive, pela data local do computador."""
        return self.repository.query(
            """SELECT exams.*, subjects.name AS subject_name FROM exams
               JOIN subjects ON subjects.id = exams.subject_id
               WHERE exam_date >= ? ORDER BY exam_date, exams.id LIMIT ?""",
            (date.today().isoformat(), limit_value(limit)))

    def save_study_note(self, topic_id: int, content: str) -> dict:
        """Acrescenta uma nota persistente a um tópico."""
        self.repository.require_topic(positive_id(topic_id))
        key = self.repository.insert("INSERT INTO study_notes(topic_id, content) VALUES (?, ?)",
                                     (topic_id, text(content, "Conteúdo")))
        return {"note_id": key}

    def get_study_notes(self, topic_id: int) -> list[dict]:
        """Consulta todas as notas de um tópico existente."""
        self.repository.require_topic(positive_id(topic_id))
        return self.repository.query("SELECT * FROM study_notes WHERE topic_id = ? ORDER BY id", (topic_id,))

    def create_exercise(self, topic_id: int, question: str, difficulty: str) -> dict:
        """Salva exercício de dificuldade easy, medium ou hard."""
        self.repository.require_topic(positive_id(topic_id))
        try:
            parsed = Difficulty(difficulty)
        except (ValueError, TypeError):
            raise ValidationError("Dificuldade deve ser easy, medium ou hard.") from None
        key = self.repository.insert("INSERT INTO exercises(topic_id, question, difficulty) VALUES (?, ?, ?)",
                                     (topic_id, text(question, "Enunciado"), parsed.value))
        return {"exercise_id": key}

    def list_exercises(self, topic_id: int) -> list[dict]:
        """Consulta enunciados e IDs antes de avaliar ou registrar tentativas."""
        self.repository.require_topic(positive_id(topic_id))
        return self.repository.query("SELECT * FROM exercises WHERE topic_id = ? ORDER BY id", (topic_id,))

    def list_attempts(self, topic_id: int, limit: int = 20) -> list[dict]:
        """Consulta respostas, erros e feedback recentes de um tópico."""
        self.repository.require_topic(positive_id(topic_id))
        return self.repository.query(
            """SELECT a.*, e.question FROM attempts a JOIN exercises e ON e.id = a.exercise_id
               WHERE e.topic_id = ? ORDER BY a.id DESC LIMIT ?""", (topic_id, limit_value(limit)))
