import logging

import models.pedido_model as pedido_model
import models.produto_model as produto_model

logger = logging.getLogger(__name__)

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
FAIXA_DESCONTO_ALTA = 10000
TAXA_DESCONTO_ALTA = 0.1
FAIXA_DESCONTO_MEDIA = 5000
TAXA_DESCONTO_MEDIA = 0.05
FAIXA_DESCONTO_BAIXA = 1000
TAXA_DESCONTO_BAIXA = 0.02


def _calcular_desconto(faturamento):
    if faturamento > FAIXA_DESCONTO_ALTA:
        return faturamento * TAXA_DESCONTO_ALTA
    if faturamento > FAIXA_DESCONTO_MEDIA:
        return faturamento * TAXA_DESCONTO_MEDIA
    if faturamento > FAIXA_DESCONTO_BAIXA:
        return faturamento * TAXA_DESCONTO_BAIXA
    return 0


def criar(dados):
    if not isinstance(dados, dict) or not dados:
        return {"erro": "Dados inválidos"}, 400
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return {"erro": "Usuario ID é obrigatório"}, 400
    if not itens or not isinstance(itens, list):
        return {"erro": "Pedido deve ter pelo menos 1 item"}, 400

    preparados = []
    estoque_restante = {}
    total = 0
    for item in itens:
        if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
            return {"erro": "Item de pedido inválido", "sucesso": False}, 400
        quantidade = item["quantidade"]
        if isinstance(quantidade, bool) or not isinstance(quantidade, int) or quantidade <= 0:
            return {"erro": "Quantidade deve ser maior que zero", "sucesso": False}, 400

        produto_id = item["produto_id"]
        produto = produto_model.buscar_por_id(produto_id)
        if produto is None:
            return {"erro": f"Produto {produto_id} não encontrado", "sucesso": False}, 400

        disponivel = estoque_restante.get(produto["id"], produto["estoque"])
        if disponivel < quantidade:
            return {"erro": f"Estoque insuficiente para {produto['nome']}", "sucesso": False}, 400
        estoque_restante[produto["id"]] = disponivel - quantidade

        total += produto["preco"] * quantidade
        preparados.append({
            "produto_id": produto["id"],
            "quantidade": quantidade,
            "preco_unitario": produto["preco"],
        })

    pedido_id = pedido_model.criar(usuario_id, total, preparados)
    logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
    logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
    return {
        "dados": {"pedido_id": pedido_id, "total": total},
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }, 201


def listar_por_usuario(usuario_id):
    return {"dados": pedido_model.listar_por_usuario(usuario_id), "sucesso": True}, 200


def listar():
    return {"dados": pedido_model.listar(), "sucesso": True}, 200


def atualizar_status(pedido_id, dados):
    dados = dados or {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        return {"erro": "Status inválido"}, 400
    pedido_model.atualizar_status(pedido_id, novo_status)
    if novo_status == "aprovado":
        logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
    if novo_status == "cancelado":
        logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200


def relatorio():
    metricas = pedido_model.obter_metricas_vendas()
    faturamento = metricas["faturamento"]
    total_pedidos = metricas["total_pedidos"]
    desconto = _calcular_desconto(faturamento)
    return {
        "dados": {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": metricas["pendentes"],
            "pedidos_aprovados": metricas["aprovados"],
            "pedidos_cancelados": metricas["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        },
        "sucesso": True,
    }, 200
