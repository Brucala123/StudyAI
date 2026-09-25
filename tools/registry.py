"""Registro explícito de funções permitidas; schema deriva dos type hints simples."""
import inspect
import json
import logging
import sqlite3
import types
from collections.abc import Callable
from typing import Any, get_args, get_origin, get_type_hints

from models.errors import ValidationError
from tools.subject_tools import SubjectTools
from tools.study_tools import StudyTools
from tools.performance_tools import PerformanceTools

logger = logging.getLogger("studyai")


def parameter_schema(annotation: Any) -> dict:
    primitives = {str: "string", int: "integer", float: "number", bool: "boolean", type(None): "null"}
    if get_origin(annotation) is types.UnionType:
        return {"type": [primitives[item] for item in get_args(annotation)]}
    return {"type": primitives[annotation]}


def matches_type(value: Any, annotation: Any) -> bool:
    if get_origin(annotation) is types.UnionType:
        return any(matches_type(value, item) for item in get_args(annotation))
    if annotation is float:
        return type(value) in (int, float)
    return type(value) is annotation


class ToolRegistry:
    def __init__(self, subjects: SubjectTools, study: StudyTools, performance: PerformanceTools):
        functions = [
            subjects.list_subjects, subjects.create_subject, subjects.list_topics, subjects.create_topic,
            study.register_study_session, study.list_recent_study_sessions,
            study.create_exam, study.list_upcoming_exams, study.save_study_note, study.get_study_notes,
            study.create_exercise, study.list_exercises, study.list_attempts,
            performance.get_topic_performance, performance.get_weak_topics, performance.register_attempt,
        ]
        self.functions: dict[str, Callable] = {function.__name__: function for function in functions}

    @property
    def schemas(self) -> list[dict]:
        schemas = []
        for name, function in self.functions.items():
            hints = get_type_hints(function)
            properties = {key: parameter_schema(hints[key]) for key in inspect.signature(function).parameters}
            schemas.append({
                "type": "function", "name": name, "description": inspect.getdoc(function),
                "strict": True, "parameters": {
                    "type": "object", "properties": properties,
                    "required": list(properties), "additionalProperties": False,
                },
            })
        return schemas

    def execute(self, name: str, arguments: str) -> str:
        try:
            if name not in self.functions:
                raise ValidationError("Ferramenta desconhecida.")
            function = self.functions[name]
            values = json.loads(arguments)
            if not isinstance(values, dict):
                raise ValidationError("Os argumentos devem ser um objeto JSON.")
            signature = inspect.signature(function)
            try:
                bound = signature.bind(**values)
            except TypeError:
                raise ValidationError("Argumentos ausentes ou desconhecidos.") from None
            bound.apply_defaults()
            hints = get_type_hints(function)
            if any(not matches_type(value, hints[key]) for key, value in bound.arguments.items()):
                raise ValidationError("Tipo de argumento inválido.")
            result = {"ok": True, "data": function(**bound.arguments)}
        except (ValidationError, json.JSONDecodeError) as error:
            message = str(error) if isinstance(error, ValidationError) else "JSON inválido."
            result = {"ok": False, "error": message}
        except sqlite3.IntegrityError:
            result = {"ok": False, "error": "Registro duplicado ou relacionamento inválido."}
        except (sqlite3.Error, OSError):
            logger.warning("Falha de persistência ao executar ferramenta.")
            result = {"ok": False, "error": "Banco indisponível. Verifique permissões e tente novamente."}
        except Exception:
            # Sem argumentos, respostas, mensagens da exceção ou segredos nos logs.
            logger.error("Falha inesperada ao executar ferramenta.")
            result = {"ok": False, "error": "Não foi possível concluir a ferramenta."}
        return json.dumps(result, ensure_ascii=False, allow_nan=False)
