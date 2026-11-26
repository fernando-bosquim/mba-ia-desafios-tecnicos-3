from models.database import get_db


def obter_metricas_vendas():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(total), 0) AS faturamento,
            SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
            SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
            SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
        FROM pedidos
        """
    )
    row = cursor.fetchone()
    return {
        "total_pedidos": row["total_pedidos"] or 0,
        "faturamento": row["faturamento"] or 0,
        "pendentes": row["pendentes"] or 0,
        "aprovados": row["aprovados"] or 0,
        "cancelados": row["cancelados"] or 0,
    }
