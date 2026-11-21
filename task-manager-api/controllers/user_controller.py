from database import db
from models.task import Task
from models.user import User
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, validate_email

def list_users():
    result = []
    for user in User.query.all():
        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "active": user.active,
            "created_at": str(user.created_at),
            "task_count": len(user.tasks),
        })
    return result, 200

def _user_tasks(user_id):
    result = []
    for task in Task.query.filter_by(user_id=user_id).all():
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": str(task.created_at),
            "due_date": str(task.due_date) if task.due_date else None,
            "overdue": task.is_overdue(),
        })
    return result

def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404
    data = user.to_dict()
    data["tasks"] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
    return data, 200

def user_tasks(user_id):
    if not db.session.get(User, user_id):
        return {"error": "Usuário não encontrado"}, 404
    return _user_tasks(user_id), 200

def create_user(data):
    if not data:
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
        return {"error": "Senha deve ter no mínimo 4 caracteres"}, 400
    if User.query.filter_by(email=email).first():
        return {"error": "Email já cadastrado"}, 409
    if role not in VALID_ROLES:
        return {"error": "Role inválido"}, 400
    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role
    db.session.add(user)
    db.session.commit()
    print(f"Usuário criado: {user.id} - {user.name}")
    return user.to_dict(), 201

def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "Usuário não encontrado"}, 404
    if not data:
        return {"error": "Dados inválidos"}, 400
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
    for task in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(task)
    db.session.delete(user)
    db.session.commit()
    print(f"Usuário deletado: {user_id}")
    return {"message": "Usuário deletado com sucesso"}, 200

def login(data):
    if not data:
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
    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
    }, 200
