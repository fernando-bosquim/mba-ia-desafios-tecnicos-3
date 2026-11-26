import logging
from models import produto_model

logger = logging.getLogger(__name__)

NOME_MIN_LEN = 2
NOME_MAX_LEN = 200
CATEGORIAS_VALIDAS = [
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
]


def _validar_payload_produto(dados):
    if not dados:
        return None, ({"erro": "Dados inválidos"}, 400)
    if "nome" not in dados:
        return None, ({"erro": "Nome é obrigatório"}, 400)
    if "preco" not in dados:
        return None, ({"erro": "Preço é obrigatório"}, 400)
    if "estoque" not in dados:
        return None, ({"erro": "Estoque é obrigatório"}, 400)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        return None, ({"erro": "Preço não pode ser negativo"}, 400)
    if estoque < 0:
        return None, ({"erro": "Estoque não pode ser negativo"}, 400)
    if len(nome) < NOME_MIN_LEN:
        return None, ({"erro": "Nome muito curto"}, 400)
    if len(nome) > NOME_MAX_LEN:
        return None, ({"erro": "Nome muito longo"}, 400)
    if categoria not in CATEGORIAS_VALIDAS:
        return None, (
            {"erro": f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}"},
            400,
        )

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }, None


def listar_produtos():
    produtos = produto_model.listar_todos()
    logger.info("Listando %d produtos", len(produtos))
    return {"dados": produtos, "sucesso": True}, 200


def buscar_produto(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        return {"erro": "Produto não encontrado", "sucesso": False}, 404
    return {"dados": produto, "sucesso": True}, 200


def criar_produto(dados):
    payload, erro = _validar_payload_produto(dados)
    if erro:
        return erro

    produto_id = produto_model.criar(**payload)
    logger.info("Produto criado com ID: %s", produto_id)
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar_produto(produto_id, dados):
    produto_existente = produto_model.buscar_por_id(produto_id)
    if not produto_existente:
        return {"erro": "Produto não encontrado"}, 404

    payload, erro = _validar_payload_produto(dados)
    if erro:
        return erro

    produto_model.atualizar(produto_id, **payload)
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar_produto(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        return {"erro": "Produto não encontrado"}, 404

    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def buscar_produtos(termo="", categoria=None, preco_min=None, preco_max=None):
    try:
        preco_min_val = float(preco_min) if preco_min not in (None, "") else None
        preco_max_val = float(preco_max) if preco_max not in (None, "") else None
    except ValueError:
        return {"erro": "Parâmetro de preço inválido"}, 400

    resultados = produto_model.buscar(termo, categoria, preco_min_val, preco_max_val)
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
