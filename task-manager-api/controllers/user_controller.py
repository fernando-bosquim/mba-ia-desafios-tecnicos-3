import logging
from sqlalchemy import func
from database import db
from middlewares.auth import generate_token
from models.task import Task
from models.user import User
from utils.helpers import (
    MIN_PASSWORD_LENGTH,
    PRIVILEGED_ROLES,
    VALID_ROLES,
    validate_email,
)

logger = logging.getLogger(__name__)


def list_users():
    rows = (
        db.session.query(User, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .all()
    )
    result = []
    for user, task_count in rows:
        user_data = user.to_dict()
        user_data["task_count"] = task_count
        result.append(user_data)
    return result, 200


def get_user_by_id(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404

    data = user.to_dict()
    tasks = Task.query.filter_by(user_id=user_id).all()
    data["tasks"] = [task.to_dict() for task in tasks]
    return data, 200


def create_user(data, current_user=None):
    if not isinstance(data, dict) or not data:
        return {"error": "Dados inválidos"}, 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not name:
        return {"error": "Nome é obrigatório"}, 400
    if not email:
        return {"error": "Email é obrigatório"}, 400
    if not password:
        return {"error": "Senha é obrigatória"}, 400

    if not validate_email(email):
        return {"error": "Email inválido"}, 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return {"error": f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"}, 400

    if role not in VALID_ROLES:
        return {"error": "Role inválido"}, 400

    if role in PRIVILEGED_ROLES:
        if not current_user or current_user.get("role") != "admin":
            return {"error": "Apenas administradores podem atribuir papel privilegiado"}, 403

    existing = User.query.filter_by(email=email).first()
    if existing:
        return {"error": "Email já cadastrado"}, 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return user.to_dict(), 201


def update_user(user_id, data, current_user=None, auth_error=None):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404

    if not isinstance(data, dict) or not data:
        return {"error": "Dados inválidos"}, 400

    if "role" in data or "active" in data:
        if auth_error in ("missing", "invalid") or current_user is None:
            return {"error": "Autenticação obrigatória para alterar papel ou status"}, 401
        if current_user.get("role") != "admin":
            return {"error": "Permissão insuficiente"}, 403

    if "name" in data:
        user.name = data["name"]

    if "email" in data:
        if not validate_email(data["email"]):
            return {"error": "Email inválido"}, 400
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            return {"error": "Email já cadastrado"}, 409
        user.email = data["email"]

    if "password" in data:
        if len(data["password"]) < MIN_PASSWORD_LENGTH:
            return {"error": "Senha muito curta"}, 400
        user.set_password(data["password"])

    if "role" in data:
        if data["role"] not in VALID_ROLES:
            return {"error": "Role inválido"}, 400
        user.role = data["role"]

    if "active" in data:
        user.active = data["active"]

    db.session.commit()
    return user.to_dict(), 200


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404

    Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: %s", user_id)
    return {"message": "Usuário deletado com sucesso"}, 200


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    for task in tasks:
        result.append(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "created_at": str(task.created_at),
                "due_date": str(task.due_date) if task.due_date else None,
                "overdue": task.is_overdue(),
            }
        )
    return result, 200


def authenticate_user(data):
    if not isinstance(data, dict) or not data:
        return {"error": "Dados inválidos"}, 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email e senha são obrigatórios"}, 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return {"error": "Credenciais inválidas"}, 401

    if not user.active:
        return {"error": "Usuário inativo"}, 403

    db.session.commit()

    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": generate_token(user),
    }, 200
