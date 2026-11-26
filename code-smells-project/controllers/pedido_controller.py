import logging
from models import pedido_model, produto_model

logger = logging.getLogger(__name__)

STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")


def criar_pedido(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return {"erro": "Usuario ID é obrigatório"}, 400
    if not itens:
        return {"erro": "Pedido deve ter pelo menos 1 item"}, 400

    produto_ids = [item["produto_id"] for item in itens]
    produtos_map = produto_model.buscar_por_ids(produto_ids)

    total = 0
    itens_resolvidos = []
    estoque_consumido = {}

    for item in itens:
        produto_id = item["produto_id"]
        quantidade = item["quantidade"]
        produto = produtos_map.get(produto_id)
        if produto is None:
            return {"erro": f"Produto {produto_id} não encontrado", "sucesso": False}, 400

        consumo_total = estoque_consumido.get(produto_id, 0) + quantidade
        if produto["estoque"] < consumo_total:
            return {"erro": f"Estoque insuficiente para {produto['nome']}", "sucesso": False}, 400

        estoque_consumido[produto_id] = consumo_total
        total += produto["preco"] * quantidade
        itens_resolvidos.append({
            "produto_id": produto_id,
            "quantidade": quantidade,
            "preco_unitario": produto["preco"],
        })

    pedido_id = pedido_model.inserir(usuario_id, total, itens_resolvidos)
    resultado = {"pedido_id": pedido_id, "total": total}

    logger.info("Notificação e-mail: Pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("Notificação SMS: Pedido %s recebido", pedido_id)
    logger.info("Notificação push: Novo pedido %s recebido pelo sistema", pedido_id)

    return {
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }, 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.listar_por_usuario(usuario_id)
    return {"dados": pedidos, "sucesso": True}, 200


def listar_todos_pedidos():
    pedidos = pedido_model.listar_todos()
    return {"dados": pedidos, "sucesso": True}, 200


def atualizar_status_pedido(pedido_id, dados):
    novo_status = (dados or {}).get("status", "")
    if novo_status not in STATUS_VALIDOS:
        return {"erro": "Status inválido"}, 400

    pedido_model.atualizar_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("Notificação: Pedido %s aprovado. Preparar envio.", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Notificação: Pedido %s cancelado. Devolver estoque.", pedido_id)

    return {"sucesso": True, "mensagem": "Status atualizado"}, 200
