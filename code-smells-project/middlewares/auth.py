from functools import wraps
from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_AUTH_SALT = "loja-api-auth"


def _get_serializer():
    secret = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret, salt=_AUTH_SALT)


def gerar_token(usuario):
    serializer = _get_serializer()
    return serializer.dumps({
        "id": usuario["id"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
    })


def extrair_usuario_opcional():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    if not token:
        return None
    max_age = current_app.config.get("TOKEN_MAX_AGE", 3600)
    try:
        return _get_serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify({"erro": "Autenticação obrigatória"}), 401
            token = header[7:].strip()
            max_age = current_app.config.get("TOKEN_MAX_AGE", 3600)
            try:
                payload = _get_serializer().loads(token, max_age=max_age)
            except (BadSignature, SignatureExpired):
                return jsonify({"erro": "Token inválido ou expirado"}), 401

            if roles and payload.get("tipo") not in roles:
                return jsonify({"erro": "Permissão insuficiente"}), 403

            g.current_user = payload
            return fn(*args, **kwargs)

        return wrapper

    return decorator
