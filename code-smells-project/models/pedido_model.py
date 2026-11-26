from models.database import get_db


def _hidratar_pedidos(rows_pedidos):
    if not rows_pedidos:
        return []

    pedidos_por_id = {}
    pedido_ids = []
    for row in rows_pedidos:
        pedido = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        }
        pedidos_por_id[row["id"]] = pedido
        pedido_ids.append(row["id"])

    placeholders = ",".join("?" * len(pedido_ids))
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        f"""
        SELECT
            ip.pedido_id,
            ip.produto_id,
            ip.quantidade,
            ip.preco_unitario,
            p.nome AS produto_nome
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({placeholders})
        """,
        tuple(pedido_ids),
    )

    for item in cursor.fetchall():
        pedidos_por_id[item["pedido_id"]]["itens"].append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] if item["produto_nome"] else "Desconhecido",
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })

    return [pedidos_por_id[pid] for pid in pedido_ids]


def inserir(usuario_id, total, itens_resolvidos):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens_resolvidos:
        cursor.execute(
            """
            INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
            """,
            (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return pedido_id


def listar_por_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    return _hidratar_pedidos(cursor.fetchall())


def listar_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    return _hidratar_pedidos(cursor.fetchall())


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    db.commit()
    return True
