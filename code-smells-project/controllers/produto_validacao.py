CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
NOME_MINIMO = 2
NOME_MAXIMO = 200

def _obrigatorios(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    if "nome" not in dados:
        return {"erro": "Nome é obrigatório"}, 400
    if "preco" not in dados:
        return {"erro": "Preço é obrigatório"}, 400
    if "estoque" not in dados:
        return {"erro": "Estoque é obrigatório"}, 400
    if dados["preco"] < 0:
        return {"erro": "Preço não pode ser negativo"}, 400
    if dados["estoque"] < 0:
        return {"erro": "Estoque não pode ser negativo"}, 400
    return None

def validar_criacao(dados):
    erro = _obrigatorios(dados)
    if erro:
        return erro
    nome = dados["nome"]
    if len(nome) < NOME_MINIMO:
        return {"erro": "Nome muito curto"}, 400
    if len(nome) > NOME_MAXIMO:
        return {"erro": "Nome muito longo"}, 400
    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        return {"erro": "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)}, 400
    return None

def validar_atualizacao(dados):
    return _obrigatorios(dados)
