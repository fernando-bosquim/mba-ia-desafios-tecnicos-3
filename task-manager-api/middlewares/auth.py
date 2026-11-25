from functools import wraps

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config.settings import SECRET_KEY, TOKEN_MAX_AGE

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="task-manager-auth")


def generate_token(user):
    """Emite token assinado para o usuário autenticado."""
    return _serializer.dumps({
        "id": user.id,
        "email": user.email,
        "role": user.role,
    })


def decode_token(token):
    """Valida a assinatura e expiração do token; retorna payload ou None."""
    try:
        return _serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def _extract_bearer():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    return token or None


def get_optional_current_user():
    """Retorna o usuário autenticado quando um Bearer token válido é enviado."""
    token = _extract_bearer()
    return decode_token(token) if token else None


def require_auth(fn):
    """Exige token Bearer válido no cabeçalho Authorization."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer()
        payload = decode_token(token) if token else None
        if not payload:
            return jsonify({"error": "Autenticação obrigatória"}), 401
        g.current_user = payload
        return fn(*args, **kwargs)
    return wrapper


def require_roles(*roles):
    """Exige usuário autenticado com um dos papéis permitidos."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = _extract_bearer()
            payload = decode_token(token) if token else None
            if not payload:
                return jsonify({"error": "Autenticação obrigatória"}), 401
            if payload.get("role") not in roles:
                return jsonify({"error": "Permissão insuficiente"}), 403
            g.current_user = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator
