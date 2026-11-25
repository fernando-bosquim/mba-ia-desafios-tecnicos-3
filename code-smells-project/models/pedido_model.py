from database import get_db


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


def criar(usuario_id, total, itens_preparados):
    """Persiste pedido, itens e baixa de estoque em transação única."""
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid
        for item in itens_preparados:
            db.execute(
                """
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        db.commit()
        return pedido_id
    except Exception:
        db.rollback()
        raise


def atualizar_status(pedido_id, novo_status):
    get_db().execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    get_db().commit()
    return True


def obter_metricas_vendas():
    """Retorna totais e contagens agregadas de pedidos sem regra de negócio."""
    db = get_db()
    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'").fetchone()[0]
    aprovados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'").fetchone()[0]
    cancelados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'").fetchone()[0]
    return {
        "total_pedidos": total_pedidos,
        "faturamento": faturamento,
        "pendentes": pendentes,
        "aprovados": aprovados,
        "cancelados": cancelados,
    }


def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
