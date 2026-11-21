from datetime import datetime

from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import utc_now
from utils.helpers import VALID_STATUSES

def _names(task):
    if task.user_id and task.user:
        user_name = task.user.name
    else:
        user_name = None
    if task.category_id and task.category:
        category_name = task.category.name
    else:
        category_name = None
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

def create_task(data):
    if not data:
        return {"error": "Dados inválidos"}, 400
    title = data.get("title")
    if not title:
        return {"error": "Título é obrigatório"}, 400
    if len(title) < 3:
        return {"error": "Título muito curto"}, 400
    if len(title) > 200:
        return {"error": "Título muito longo"}, 400

    status = data.get("status", "pending")
    priority = data.get("priority", 3)
    user_id = data.get("user_id")
    category_id = data.get("category_id")
    if status not in VALID_STATUSES:
        return {"error": "Status inválido"}, 400
    if priority < 1 or priority > 5:
        return {"error": "Prioridade deve ser entre 1 e 5"}, 400
    if user_id and not db.session.get(User, user_id):
        return {"error": "Usuário não encontrado"}, 404
    if category_id and not db.session.get(Category, category_id):
        return {"error": "Categoria não encontrada"}, 404

    task = Task()
    task.title = title
    task.description = data.get("description", "")
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id
    if data.get("due_date"):
        parsed, erro = _parse_due_date(data.get("due_date"))
        if erro:
            return erro, 400
        task.due_date = parsed
    tags = data.get("tags")
    if tags:
        task.tags = ",".join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    print(f"Task criada: {task.id} - {task.title}")
    return task.to_dict(), 201

def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    if not data:
        return {"error": "Dados inválidos"}, 400
    if "title" in data:
        if len(data["title"]) < 3:
            return {"error": "Título muito curto"}, 400
        if len(data["title"]) > 200:
            return {"error": "Título muito longo"}, 400
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return {"error": "Status inválido"}, 400
        task.status = data["status"]
    if "priority" in data:
        if data["priority"] < 1 or data["priority"] > 5:
            return {"error": "Prioridade deve ser entre 1 e 5"}, 400
        task.priority = data["priority"]
    if "user_id" in data:
        if data["user_id"] and not db.session.get(User, data["user_id"]):
            return {"error": "Usuário não encontrado"}, 404
        task.user_id = data["user_id"]
    if "category_id" in data:
        if data["category_id"] and not db.session.get(Category, data["category_id"]):
            return {"error": "Categoria não encontrada"}, 404
        task.category_id = data["category_id"]
    if "due_date" in data:
        if data["due_date"]:
            parsed, erro = _parse_due_date(data["due_date"])
            if erro:
                return {"error": "Formato de data inválido"}, 400
            task.due_date = parsed
        else:
            task.due_date = None
    if "tags" in data:
        tags = data["tags"]
        task.tags = ",".join(tags) if isinstance(tags, list) else tags
    task.updated_at = utc_now()
    db.session.commit()
    print(f"Task atualizada: {task.id}")
    return task.to_dict(), 200

def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    db.session.delete(task)
    db.session.commit()
    print(f"Task deletada: {task_id}")
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
        query = query.filter(Task.priority == int(priority))
    if user_id:
        query = query.filter(Task.user_id == int(user_id))
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
