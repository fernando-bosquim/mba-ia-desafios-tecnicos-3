from functools import wraps

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config.settings import SECRET_KEY, TOKEN_MAX_AGE

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="loja-auth")


def gerar_token(usuario):
    """Emite token assinado para o usuário autenticado."""
    return _serializer.dumps({
        "id": usuario["id"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
    })


def validar_token(token):
    """Valida a assinatura e expiração do token; retorna payload ou None."""
    try:
        return _serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def _extrair_bearer():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    return token or None


def require_auth(fn):
    """Exige token Bearer válido no cabeçalho Authorization."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extrair_bearer()
        payload = validar_token(token) if token else None
        if not payload:
            return jsonify({"erro": "Autenticação obrigatória"}), 401
        g.current_user = payload
        return fn(*args, **kwargs)
    return wrapper


def require_admin(fn):
    """Exige usuário autenticado com papel 'admin'."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extrair_bearer()
        payload = validar_token(token) if token else None
        if not payload:
            return jsonify({"erro": "Autenticação obrigatória"}), 401
        if payload.get("tipo") != "admin":
            return jsonify({"erro": "Acesso restrito a administradores"}), 403
        g.current_user = payload
        return fn(*args, **kwargs)
    return wrapper
