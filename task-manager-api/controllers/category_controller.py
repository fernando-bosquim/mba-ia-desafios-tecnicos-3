from sqlalchemy import func
from database import db
from models.category import Category
from models.task import Task
from utils.helpers import DEFAULT_COLOR


def list_categories():
    rows = (
        db.session.query(Category, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .all()
    )
    result = []
    for category, task_count in rows:
        cat_data = category.to_dict()
        cat_data["task_count"] = task_count
        result.append(cat_data)
    return result, 200


def create_category(data):
    if not isinstance(data, dict) or not data:
        return {"error": "Dados inválidos"}, 400

    name = data.get("name")
    if not name:
        return {"error": "Nome é obrigatório"}, 400

    category = Category(
        name=name,
        description=data.get("description", ""),
        color=data.get("color", DEFAULT_COLOR),
    )
    db.session.add(category)
    db.session.commit()
    return category.to_dict(), 201


def update_category(cat_id, data):
    category = db.session.get(Category, cat_id)
    if not category:
        return {"error": "Categoria não encontrada"}, 404

    if not isinstance(data, dict) or not data:
        return {"error": "Dados inválidos"}, 400

    if "name" in data:
        category.name = data["name"]
    if "description" in data:
        category.description = data["description"]
    if "color" in data:
        category.color = data["color"]

    db.session.commit()
    return category.to_dict(), 200


def delete_category(cat_id):
    category = db.session.get(Category, cat_id)
    if not category:
        return {"error": "Categoria não encontrada"}, 404

    db.session.delete(category)
    db.session.commit()
    return {"message": "Categoria deletada"}, 200
