from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import utc_now
from utils.helpers import DEFAULT_COLOR

def summary():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()
    pending = Task.query.filter_by(status="pending").count()
    in_progress = Task.query.filter_by(status="in_progress").count()
    done = Task.query.filter_by(status="done").count()
    cancelled = Task.query.filter_by(status="cancelled").count()
    priorities = {level: Task.query.filter_by(priority=level).count() for level in range(1, 6)}

    overdue_list = []
    for task in Task.query.all():
        if not task.is_overdue():
            continue
        overdue_list.append({
            "id": task.id,
            "title": task.title,
            "due_date": str(task.due_date),
            "days_overdue": (utc_now() - task.due_date).days,
        })

    seven_days_ago = utc_now() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(Task.status == "done", Task.updated_at >= seven_days_ago).count()

    user_stats = []
    for user in User.query.options(joinedload(User.tasks)).all():
        total = len(user.tasks)
        completed = sum(1 for task in user.tasks if task.status == "done")
        user_stats.append({
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": round((completed / total) * 100, 2) if total > 0 else 0,
        })

    return {
        "generated_at": str(utc_now()),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "cancelled": cancelled,
        },
        "tasks_by_priority": {
            "critical": priorities[1],
            "high": priorities[2],
            "medium": priorities[3],
            "low": priorities[4],
            "minimal": priorities[5],
        },
        "overdue": {"count": len(overdue_list), "tasks": overdue_list},
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }, 200

def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404
    tasks = Task.query.filter_by(user_id=user_id).all()
    done = pending = in_progress = cancelled = overdue = high_priority = 0
    for task in tasks:
        if task.status == "done":
            done += 1
        elif task.status == "pending":
            pending += 1
        elif task.status == "in_progress":
            in_progress += 1
        elif task.status == "cancelled":
            cancelled += 1
        if task.priority <= 2:
            high_priority += 1
        if task.is_overdue():
            overdue += 1
    total = len(tasks)
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        },
    }, 200

def list_categories():
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
    )
    result = []
    for category in Category.query.all():
        data = category.to_dict()
        data["task_count"] = counts.get(category.id, 0)
        result.append(data)
    return result, 200

def create_category(data):
    if not data:
        return {"error": "Dados inválidos"}, 400
    name = data.get("name")
    if not name:
        return {"error": "Nome é obrigatório"}, 400
    category = Category()
    category.name = name
    category.description = data.get("description", "")
    category.color = data.get("color", DEFAULT_COLOR)
    db.session.add(category)
    db.session.commit()
    return category.to_dict(), 201

def update_category(category_id, data):
    category = db.session.get(Category, category_id)
    if not category:
        return {"error": "Categoria não encontrada"}, 404
    data = data or {}
    if "name" in data:
        category.name = data["name"]
    if "description" in data:
        category.description = data["description"]
    if "color" in data:
        category.color = data["color"]
    db.session.commit()
    return category.to_dict(), 200

def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        return {"error": "Categoria não encontrada"}, 404
    db.session.delete(category)
    db.session.commit()
    return {"message": "Categoria deletada"}, 200
