import logging
from config.settings import APP_ENV, APP_VERSION
from models import admin_model

logger = logging.getLogger(__name__)


def index():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }, 200


def health_check():
    counts = admin_model.obter_contagens_health()
    return {
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": APP_VERSION,
        "ambiente": APP_ENV,
    }, 200


def reset_database():
    admin_model.resetar_tabelas()
    logger.warning("Banco de dados resetado por ação administrativa")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200


def executar_query():
    return {"erro": "Execução de SQL arbitrário não é permitida"}, 400
