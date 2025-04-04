from datetime import datetime


def format_error_response(message: str | None):
    """Форматирует JSON-ответ с ошибкой."""
    return {
        "success": False,
        "data": None,
        "message": message,
        "successMessage": None
    }


def serialize_datetimes(data: dict) -> dict:
    """
    Преобразует все значения типа datetime в словаре data в строки (isoformat).
    """
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data
