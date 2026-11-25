import logging

from database import ping_db, reset_db
import models.pedido_model as pedido_model
import models.produto_model as produto_model
import models.usuario_model as usuario_model

logger = logging.getLogger(__name__)


def health():
    ping_db()
    return {
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(),
            "usuarios": usuario_model.contar(),
            "pedidos": pedido_model.contar(),
        },
        "versao": "1.0.0",
        "ambiente": "producao",
    }, 200


def resetar():
    reset_db()
    logger.warning("Banco de dados resetado por administrador autenticado")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200


def recusar_sql(dados):
    query = (dados if isinstance(dados, dict) else {}).get("sql", "")
    if not query:
        return {"erro": "Query não informada"}, 400
    return {"erro": "Query não permitida"}, 400
