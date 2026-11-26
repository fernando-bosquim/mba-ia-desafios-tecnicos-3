import logging
from middlewares.auth import gerar_token
from models import usuario_model

logger = logging.getLogger(__name__)

TIPO_PADRAO = "cliente"


def listar_usuarios():
    usuarios = usuario_model.listar_todos()
    return {"dados": usuarios, "sucesso": True}, 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        return {"erro": "Usuário não encontrado"}, 404
    return {"dados": usuario, "sucesso": True}, 200


def criar_usuario(dados, usuario_autenticado=None):
    if not dados:
        return {"erro": "Dados inválidos"}, 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    tipo = dados.get("tipo", TIPO_PADRAO)

    if not nome or not email or not senha:
        return {"erro": "Nome, email e senha são obrigatórios"}, 400

    if tipo != TIPO_PADRAO:
        if not usuario_autenticado or usuario_autenticado.get("tipo") != "admin":
            return {"erro": "Permissão insuficiente para definir tipo privilegiado"}, 403

    usuario_id = usuario_model.criar(nome, email, senha, tipo=tipo)
    logger.info("Usuário criado: %s", email)
    return {"dados": {"id": usuario_id}, "sucesso": True}, 201


def login(dados):
    if not dados:
        return {"erro": "Email e senha são obrigatórios"}, 400

    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return {"erro": "Email e senha são obrigatórios"}, 400

    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("Login falhou: %s", email)
        return {"erro": "Email ou senha inválidos", "sucesso": False}, 401

    token = gerar_token(usuario)
    logger.info("Login bem-sucedido: %s", email)
    return {
        "dados": usuario,
        "token": token,
        "sucesso": True,
        "mensagem": "Login OK",
    }, 200
