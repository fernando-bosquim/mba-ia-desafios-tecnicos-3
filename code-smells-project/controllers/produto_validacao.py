CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
NOME_MINIMO = 2
NOME_MAXIMO = 200


def validar_produto(dados):
    """Valida campos obrigatórios, faixa numérica, tamanho de nome e categoria de produto."""
    if not isinstance(dados, dict) or not dados:
        return {"erro": "Dados inválidos"}, 400
    if "nome" not in dados:
        return {"erro": "Nome é obrigatório"}, 400
    if "preco" not in dados:
        return {"erro": "Preço é obrigatório"}, 400
    if "estoque" not in dados:
        return {"erro": "Estoque é obrigatório"}, 400

    nome = dados["nome"]
    if not isinstance(nome, str):
        return {"erro": "Nome inválido"}, 400
    if len(nome) < NOME_MINIMO:
        return {"erro": "Nome muito curto"}, 400
    if len(nome) > NOME_MAXIMO:
        return {"erro": "Nome muito longo"}, 400

    preco = dados["preco"]
    if isinstance(preco, bool) or not isinstance(preco, (int, float)):
        return {"erro": "Preço inválido"}, 400
    if preco < 0:
        return {"erro": "Preço não pode ser negativo"}, 400

    estoque = dados["estoque"]
    if isinstance(estoque, bool) or not isinstance(estoque, int):
        return {"erro": "Estoque inválido"}, 400
    if estoque < 0:
        return {"erro": "Estoque não pode ser negativo"}, 400

    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        return {"erro": "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)}, 400
    return None
