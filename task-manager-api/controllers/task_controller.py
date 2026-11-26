import logging
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import (
    calculate_percentage,
    utc_now,
    validate_task_payload,
)

logger = logging.getLogger(__name__)


def list_tasks():
    tasks = (
        Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category),
        ).all()
    )
    result = []
    for task in tasks:
        task_data = task.to_dict()
        task_data["overdue"] = task.is_overdue()
        task_data["user_name"] = task.user.name if task.user else None
        task_data["category_name"] = task.category.name if task.category else None
        result.append(task_data)
    return result, 200


def get_task_by_id(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    data = task.to_dict()
    data["overdue"] = task.is_overdue()
    return data, 200


def create_task(data):
    cleaned, error = validate_task_payload(data, require_title=True)
    if error:
        return {"error": error}, 400

    user_id = cleaned.get("user_id")
    if user_id and not db.session.get(User, user_id):
        return {"error": "Usuário não encontrado"}, 404

    category_id = cleaned.get("category_id")
    if category_id and not db.session.get(Category, category_id):
        return {"error": "Categoria não encontrada"}, 404

    task = Task(
        title=cleaned["title"],
        description=cleaned.get("description", ""),
        status=cleaned.get("status", "pending"),
        priority=cleaned.get("priority", 3),
        user_id=user_id,
        category_id=category_id,
        due_date=cleaned.get("due_date"),
        tags=cleaned.get("tags"),
    )
    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: %s - %s", task.id, task.title)
    return task.to_dict(), 201


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404

    cleaned, error = validate_task_payload(data, require_title=False)
    if error:
        return {"error": error}, 400

    if "user_id" in cleaned and cleaned["user_id"]:
        if not db.session.get(User, cleaned["user_id"]):
            return {"error": "Usuário não encontrado"}, 404

    if "category_id" in cleaned and cleaned["category_id"]:
        if not db.session.get(Category, cleaned["category_id"]):
            return {"error": "Categoria não encontrada"}, 404

    for field, value in cleaned.items():
        setattr(task, field, value)

    task.updated_at = utc_now()
    db.session.commit()
    logger.info("Task atualizada: %s", task.id)
    return task.to_dict(), 200


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404

    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: %s", task_id)
    return {"message": "Task deletada com sucesso"}, 200


def search_tasks(query_text="", status="", priority="", user_id=""):
    tasks = Task.query

    if query_text:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f"%{query_text}%"),
                Task.description.like(f"%{query_text}%"),
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        try:
            priority_int = int(priority)
        except ValueError:
            return {"error": "Parâmetro priority inválido"}, 400
        tasks = tasks.filter(Task.priority == priority_int)

    if user_id:
        try:
            user_id_int = int(user_id)
        except ValueError:
            return {"error": "Parâmetro user_id inválido"}, 400
        tasks = tasks.filter(Task.user_id == user_id_int)

    return [task.to_dict() for task in tasks.all()], 200


def get_task_stats():
    status_rows = (
        db.session.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    status_counts = dict(status_rows)
    total = sum(status_counts.values())
    done = status_counts.get("done", 0)

    tasks_with_due_date = Task.query.filter(Task.due_date.isnot(None)).all()
    overdue_count = sum(1 for task in tasks_with_due_date if task.is_overdue())

    return {
        "total": total,
        "pending": status_counts.get("pending", 0),
        "in_progress": status_counts.get("in_progress", 0),
        "done": done,
        "cancelled": status_counts.get("cancelled", 0),
        "overdue": overdue_count,
        "completion_rate": calculate_percentage(done, total),
    }, 200
