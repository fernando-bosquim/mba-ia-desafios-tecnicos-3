import models.pedido_model as pedido_model

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

def criar(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return {"erro": "Usuario ID é obrigatório"}, 400
    if not itens:
        return {"erro": "Pedido deve ter pelo menos 1 item"}, 400
    resultado = pedido_model.criar(usuario_id, itens)
    if "erro" in resultado:
        return {"erro": resultado["erro"], "sucesso": False}, 400
    print(f"ENVIANDO EMAIL: Pedido {resultado['pedido_id']} criado para usuario {usuario_id}")
    print("ENVIANDO SMS: Seu pedido foi recebido!")
    print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201

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
        print(f"NOTIFICAÇÃO: Pedido {pedido_id} foi aprovado! Preparar envio.")
    if novo_status == "cancelado":
        print(f"NOTIFICAÇÃO: Pedido {pedido_id} cancelado. Devolver estoque.")
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200

def relatorio():
    return {"dados": pedido_model.relatorio_vendas(), "sucesso": True}, 200
