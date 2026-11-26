from datetime import datetime, timezone
import re

VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
VALID_ROLES = ("user", "admin", "manager")
PRIVILEGED_ROLES = ("admin", "manager")
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_COLOR = "#000000"

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def utc_now():
    return datetime.now(timezone.utc)


def normalize_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    if not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email))


def parse_date(date_string):
    if not isinstance(date_string, str):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None


def validate_task_payload(data, require_title=False):
    if not isinstance(data, dict) or not data:
        return None, "Dados inválidos"

    result = {}

    if require_title or "title" in data:
        title = data.get("title")
        if not title:
            return None, "Título é obrigatório"
        if not isinstance(title, str):
            return None, "Título inválido"
        if len(title) < MIN_TITLE_LENGTH:
            return None, "Título muito curto"
        if len(title) > MAX_TITLE_LENGTH:
            return None, "Título muito longo"
        result["title"] = title

    if "description" in data:
        result["description"] = data["description"]
    elif require_title:
        result["description"] = ""

    if "status" in data:
        status = data["status"]
        if status not in VALID_STATUSES:
            return None, "Status inválido"
        result["status"] = status
    elif require_title:
        result["status"] = "pending"

    if "priority" in data:
        priority = data["priority"]
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            return None, "Prioridade deve ser entre 1 e 5"
        result["priority"] = priority
    elif require_title:
        result["priority"] = DEFAULT_PRIORITY

    if "user_id" in data:
        result["user_id"] = data["user_id"]

    if "category_id" in data:
        result["category_id"] = data["category_id"]

    if "due_date" in data:
        due_date = data["due_date"]
        if due_date:
            parsed = parse_date(due_date)
            if not parsed:
                return None, "Formato de data inválido. Use YYYY-MM-DD"
            result["due_date"] = parsed
        else:
            result["due_date"] = None

    if "tags" in data:
        tags = data["tags"]
        if isinstance(tags, list):
            result["tags"] = ",".join(str(tag) for tag in tags)
        else:
            result["tags"] = tags

    return result, None
