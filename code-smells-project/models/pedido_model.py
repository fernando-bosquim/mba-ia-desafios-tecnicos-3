from database import get_db

FAIXA_DESCONTO_ALTA = 10000
TAXA_DESCONTO_ALTA = 0.1
FAIXA_DESCONTO_MEDIA = 5000
TAXA_DESCONTO_MEDIA = 0.05
FAIXA_DESCONTO_BAIXA = 1000
TAXA_DESCONTO_BAIXA = 0.02

def _agrupar(rows):
    pedidos = []
    indice = {}
    for row in rows:
        pedido_id = row["id"]
        if pedido_id not in indice:
            pedido = {
                "id": pedido_id,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            indice[pedido_id] = pedido
            pedidos.append(pedido)
        if row["item_id"] is None:
            continue
        nome = row["produto_nome"] if row["produto_nome"] else "Desconhecido"
        indice[pedido_id]["itens"].append({
            "produto_id": row["produto_id"],
            "produto_nome": nome,
            "quantidade": row["quantidade"],
            "preco_unitario": row["preco_unitario"],
        })
    return pedidos

def _consultar(where="", params=()):
    query = """
        SELECT
            p.id, p.usuario_id, p.status, p.total, p.criado_em,
            i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
    """
    if where:
        query += " WHERE " + where
    query += " ORDER BY p.id, i.id"
    return _agrupar(get_db().execute(query, params).fetchall())

def listar_por_usuario(usuario_id):
    return _consultar("p.usuario_id = ?", (usuario_id,))

def listar():
    return _consultar()

def criar(usuario_id, itens):
    db = get_db()
    preparados = []
    total = 0
    for item in itens:
        produto = db.execute(
            "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
            (item["produto_id"],),
        ).fetchone()
        if produto is None:
            return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente para " + produto["nome"]}
        total = total + (produto["preco"] * item["quantidade"])
        preparados.append((item, produto))

    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid
    for item, produto in preparados:
        db.execute(
            """
            INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
            """,
            (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
        )
        db.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )
    db.commit()
    return {"pedido_id": pedido_id, "total": total}

def atualizar_status(pedido_id, novo_status):
    get_db().execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    get_db().commit()
    return True

def relatorio_vendas():
    db = get_db()
    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0]
    if faturamento is None:
        faturamento = 0
    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'").fetchone()[0]
    aprovados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'").fetchone()[0]
    cancelados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'").fetchone()[0]

    desconto = 0
    if faturamento > FAIXA_DESCONTO_ALTA:
        desconto = faturamento * TAXA_DESCONTO_ALTA
    elif faturamento > FAIXA_DESCONTO_MEDIA:
        desconto = faturamento * TAXA_DESCONTO_MEDIA
    elif faturamento > FAIXA_DESCONTO_BAIXA:
        desconto = faturamento * TAXA_DESCONTO_BAIXA

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }

def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

def limpar():
    db = get_db()
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    db.execute("DELETE FROM produtos")
    db.execute("DELETE FROM usuarios")
    db.commit()

def ping():
    get_db().execute("SELECT 1").fetchone()
