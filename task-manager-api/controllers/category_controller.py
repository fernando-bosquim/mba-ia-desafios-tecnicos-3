from sqlalchemy import func

from database import db
from models.category import Category
from models.task import Task
from utils.helpers import DEFAULT_COLOR


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
    if not isinstance(data, dict) or not data:
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
    data = data if isinstance(data, dict) else {}
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
