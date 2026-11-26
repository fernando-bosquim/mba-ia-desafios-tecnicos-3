from functools import wraps
from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="task-manager-auth")


def generate_token(user):
    payload = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }
    return _get_serializer().dumps(payload)


def extract_token_payload():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, "missing"
    token = header[7:].strip()
    if not token:
        return None, "missing"
    max_age = current_app.config.get("TOKEN_MAX_AGE", 3600)
    try:
        payload = _get_serializer().loads(token, max_age=max_age)
        return payload, None
    except (BadSignature, SignatureExpired):
        return None, "invalid"


def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            payload, err = extract_token_payload()
            if err == "missing":
                return jsonify({"error": "Autenticação obrigatória"}), 401
            if err == "invalid":
                return jsonify({"error": "Token inválido ou expirado"}), 401
            if roles and payload.get("role") not in roles:
                return jsonify({"error": "Permissão insuficiente"}), 403
            g.current_user = payload
            return fn(*args, **kwargs)

        return wrapper

    return decorator
