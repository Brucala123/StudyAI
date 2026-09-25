from datetime import date, datetime, timezone
from models.errors import ValidationError


def text(value: str, label: str, *, required: bool = True) -> str:
    if not isinstance(value, str) or len(value) > 20000:
        raise ValidationError(f"{label}: use texto de até 20000 caracteres.")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{label} não pode ficar vazio.")
    return value


def positive_id(value: int) -> int:
    if type(value) is not int or value < 1:
        raise ValidationError("Use um identificador inteiro positivo.")
    return value


def limit_value(value: int) -> int:
    if type(value) is not int or not 1 <= value <= 100:
        raise ValidationError("O limite deve estar entre 1 e 100.")
    return value


def iso_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return value
    except (TypeError, ValueError):
        raise ValidationError("Use uma data válida no formato AAAA-MM-DD.") from None


def iso_timestamp(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        raise ValidationError("Use data e hora ISO com fuso, como 2026-09-24T18:00:00-03:00.") from None
