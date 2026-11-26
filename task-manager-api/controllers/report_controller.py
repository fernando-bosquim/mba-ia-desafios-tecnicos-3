from datetime import timedelta
from sqlalchemy import case, func
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, normalize_utc, utc_now


def get_summary_report():
    now = utc_now()
    seven_days_ago_naive = now.replace(tzinfo=None) - timedelta(days=7)

    total_users = db.session.query(func.count(User.id)).scalar() or 0
    total_categories = db.session.query(func.count(Category.id)).scalar() or 0

    status_counts = dict(
        db.session.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    priority_counts = dict(
        db.session.query(Task.priority, func.count(Task.id))
        .group_by(Task.priority)
        .all()
    )
    total_tasks = sum(status_counts.values())

    tasks_with_due_date = Task.query.filter(Task.due_date.isnot(None)).all()
    overdue_list = []
    for task in tasks_with_due_date:
        if task.is_overdue():
            overdue_list.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": str(task.due_date),
                    "days_overdue": (now - normalize_utc(task.due_date)).days,
                }
            )

    recent_tasks = (
        db.session.query(func.count(Task.id))
        .filter(Task.created_at >= seven_days_ago_naive)
        .scalar()
        or 0
    )
    recent_done = (
        db.session.query(func.count(Task.id))
        .filter(Task.status == "done", Task.updated_at >= seven_days_ago_naive)
        .scalar()
        or 0
    )

    user_rows = (
        db.session.query(
            User.id,
            User.name,
            func.count(Task.id).label("total_tasks"),
            func.coalesce(
                func.sum(case((Task.status == "done", 1), else_=0)),
                0,
            ).label("completed_tasks"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
        .all()
    )
    user_stats = [
        {
            "user_id": row.id,
            "user_name": row.name,
            "total_tasks": row.total_tasks,
            "completed_tasks": int(row.completed_tasks),
            "completion_rate": calculate_percentage(int(row.completed_tasks), row.total_tasks),
        }
        for row in user_rows
    ]

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": status_counts.get("pending", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "done": status_counts.get("done", 0),
            "cancelled": status_counts.get("cancelled", 0),
        },
        "tasks_by_priority": {
            "critical": priority_counts.get(1, 0),
            "high": priority_counts.get(2, 0),
            "medium": priority_counts.get(3, 0),
            "low": priority_counts.get(4, 0),
            "minimal": priority_counts.get(5, 0),
        },
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }, 200


def get_user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    status_counts = {"done": 0, "pending": 0, "in_progress": 0, "cancelled": 0}
    overdue = 0
    high_priority = 0

    for task in tasks:
        if task.status in status_counts:
            status_counts[task.status] += 1
        if task.priority <= 2:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "statistics": {
            "total_tasks": total,
            "done": status_counts["done"],
            "pending": status_counts["pending"],
            "in_progress": status_counts["in_progress"],
            "cancelled": status_counts["cancelled"],
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": calculate_percentage(status_counts["done"], total),
        },
    }, 200
