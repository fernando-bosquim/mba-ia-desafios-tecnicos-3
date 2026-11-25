import logging

import models.produto_model as produto_model
from controllers.produto_validacao import validar_produto

logger = logging.getLogger(__name__)


def listar():
    produtos = produto_model.listar()
    logger.info("Listando %d produtos", len(produtos))
    return {"dados": produtos, "sucesso": True}, 200


def buscar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto:
        return {"dados": produto, "sucesso": True}, 200
    return {"erro": "Produto não encontrado", "sucesso": False}, 404


def criar(dados):
    erro = validar_produto(dados)
    if erro:
        return erro
    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", "geral")
    produto_id = produto_model.criar(nome, descricao, dados["preco"], dados["estoque"], categoria)
    logger.info("Produto criado com ID: %s", produto_id)
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar(produto_id, dados):
    if not produto_model.buscar_por_id(produto_id):
        return {"erro": "Produto não encontrado"}, 404
    erro = validar_produto(dados)
    if erro:
        return erro
    produto_model.atualizar(
        produto_id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        return {"erro": "Produto não encontrado"}, 404
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def _parse_preco(valor):
    if valor is None or valor == "":
        return None
    return float(valor)


def buscar_filtros(termo, categoria, preco_min, preco_max):
    try:
        min_val = _parse_preco(preco_min)
        max_val = _parse_preco(preco_max)
    except ValueError:
        return {"erro": "Parâmetro de preço inválido"}, 400
    resultados = produto_model.buscar(termo, categoria, min_val, max_val)
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
