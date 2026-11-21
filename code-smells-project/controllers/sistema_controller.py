from config.settings import DATABASE_PATH, DEBUG
import models.pedido_model as pedido_model
import models.produto_model as produto_model
import models.usuario_model as usuario_model

def health():
    pedido_model.ping()
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
        "db_path": DATABASE_PATH,
        "debug": DEBUG,
    }, 200

def resetar():
    pedido_model.limpar()
    print("!!! BANCO DE DADOS RESETADO !!!")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200

def recusar_sql(dados):
    query = (dados or {}).get("sql", "")
    if not query:
        return {"erro": "Query não informada"}, 400
    return {"erro": "Query não permitida"}, 400
