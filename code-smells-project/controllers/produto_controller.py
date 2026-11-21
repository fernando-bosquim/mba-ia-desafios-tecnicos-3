import models.produto_model as produto_model
from controllers.produto_validacao import validar_atualizacao, validar_criacao

def listar():
    produtos = produto_model.listar()
    print(f"Listando {len(produtos)} produtos")
    return {"dados": produtos, "sucesso": True}, 200

def buscar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto:
        return {"dados": produto, "sucesso": True}, 200
    return {"erro": "Produto não encontrado", "sucesso": False}, 404

def criar(dados):
    erro = validar_criacao(dados)
    if erro:
        return erro
    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", "geral")
    produto_id = produto_model.criar(nome, descricao, dados["preco"], dados["estoque"], categoria)
    print(f"Produto criado com ID: {produto_id}")
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201

def atualizar(produto_id, dados):
    if not produto_model.buscar_por_id(produto_id):
        return {"erro": "Produto não encontrado"}, 404
    erro = validar_atualizacao(dados)
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
    print(f"Produto {produto_id} deletado")
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200

def buscar_filtros(termo, categoria, preco_min, preco_max):
    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)
    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
