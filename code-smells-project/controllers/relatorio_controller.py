from models import relatorio_model

FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)


def _calcular_desconto(faturamento):
    for limite, aliquota in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * aliquota
    return 0


def relatorio_vendas():
    metricas = relatorio_model.obter_metricas_vendas()
    total_pedidos = metricas["total_pedidos"]
    faturamento = metricas["faturamento"]
    desconto = _calcular_desconto(faturamento)

    dados = {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": metricas["pendentes"],
        "pedidos_aprovados": metricas["aprovados"],
        "pedidos_cancelados": metricas["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
    return {"dados": dados, "sucesso": True}, 200
