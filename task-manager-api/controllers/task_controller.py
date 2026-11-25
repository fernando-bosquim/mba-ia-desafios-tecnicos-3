import logging
from datetime import datetime

from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import utc_now
from utils.helpers import (
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_STATUSES,
)

logger = logging.getLogger(__name__)


def _names(task):
    user_name = task.user.name if task.user_id and task.user else None
    category_name = task.category.name if task.category_id and task.category else None
    return user_name, category_name


def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for task in tasks:
        data = task.to_dict()
        data["overdue"] = task.is_overdue()
        user_name, category_name = _names(task)
        data["user_name"] = user_name
        data["category_name"] = category_name
        result.append(data)
    return result, 200


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    data = task.to_dict()
    data["overdue"] = task.is_overdue()
    return data, 200


def _parse_due_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d"), None
    except (TypeError, ValueError):
        return None, {"error": "Formato de data inválido. Use YYYY-MM-DD"}


def _validate_task_payload(data, require_title=False):
    """Valida campos comuns entre criação e atualização de tarefas."""
    if not isinstance(data, dict) or not data:
        return None, ({"error": "Dados inválidos"}, 400)

    fields = {}
    if require_title or "title" in data:
        title = data.get("title")
        if require_title and not title:
            return None, ({"error": "Título é obrigatório"}, 400)
        if not isinstance(title, str):
            return None, ({"error": "Título inválido"}, 400)
        if len(title) < MIN_TITLE_LENGTH:
            return None, ({"error": "Título muito curto"}, 400)
        if len(title) > MAX_TITLE_LENGTH:
            return None, ({"error": "Título muito longo"}, 400)
        fields["title"] = title

    if "description" in data:
        fields["description"] = data["description"]
    elif require_title:
        fields["description"] = ""

    if require_title or "status" in data:
        status = data.get("status", "pending") if require_title else data["status"]
        if status not in VALID_STATUSES:
            return None, ({"error": "Status inválido"}, 400)
        fields["status"] = status

    if require_title or "priority" in data:
        priority = data.get("priority", DEFAULT_PRIORITY) if require_title else data["priority"]
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            return None, ({"error": f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}"}, 400)
        fields["priority"] = priority

    if require_title or "user_id" in data:
        user_id = data.get("user_id")
        if user_id and not db.session.get(User, user_id):
            return None, ({"error": "Usuário não encontrado"}, 404)
        fields["user_id"] = user_id

    if require_title or "category_id" in data:
        category_id = data.get("category_id")
        if category_id and not db.session.get(Category, category_id):
            return None, ({"error": "Categoria não encontrada"}, 404)
        fields["category_id"] = category_id

    if "due_date" in data:
        if data["due_date"]:
            parsed, erro = _parse_due_date(data["due_date"])
            if erro:
                return None, (erro, 400)
            fields["due_date"] = parsed
        else:
            fields["due_date"] = None

    if "tags" in data:
        tags = data["tags"]
        if tags or not require_title:
            fields["tags"] = ",".join(tags) if isinstance(tags, list) else tags

    return fields, None


def create_task(data):
    fields, erro = _validate_task_payload(data, require_title=True)
    if erro:
        return erro
    task = Task()
    for key, value in fields.items():
        setattr(task, key, value)
    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: %s - %s", task.id, task.title)
    return task.to_dict(), 201


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    fields, erro = _validate_task_payload(data, require_title=False)
    if erro:
        return erro
    for key, value in fields.items():
        setattr(task, key, value)
    task.updated_at = utc_now()
    db.session.commit()
    logger.info("Task atualizada: %s", task.id)
    return task.to_dict(), 200


def delete_task(task_id, current_user):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    if current_user.get("role") not in ("admin", "manager") and task.user_id != current_user.get("id"):
        return {"error": "Permissão insuficiente"}, 403
    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: %s", task_id)
    return {"message": "Task deletada com sucesso"}, 200


def search_tasks(filters):
    query = Task.query
    termo = filters.get("q", "")
    status = filters.get("status", "")
    priority = filters.get("priority", "")
    user_id = filters.get("user_id", "")
    if termo:
        query = query.filter(db.or_(Task.title.like(f"%{termo}%"), Task.description.like(f"%{termo}%")))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        try:
            query = query.filter(Task.priority == int(priority))
        except ValueError:
            return {"error": "Filtro numérico inválido"}, 400
    if user_id:
        try:
            query = query.filter(Task.user_id == int(user_id))
        except ValueError:
            return {"error": "Filtro numérico inválido"}, 400
    return [task.to_dict() for task in query.all()], 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status="pending").count()
    in_progress = Task.query.filter_by(status="in_progress").count()
    done = Task.query.filter_by(status="done").count()
    cancelled = Task.query.filter_by(status="cancelled").count()
    overdue_count = sum(1 for task in Task.query.all() if task.is_overdue())
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "done": done,
        "cancelled": cancelled,
        "overdue": overdue_count,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }, 200
