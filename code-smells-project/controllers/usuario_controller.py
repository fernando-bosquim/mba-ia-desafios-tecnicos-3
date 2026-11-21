import models.usuario_model as usuario_model

def listar():
    return {"dados": usuario_model.listar(), "sucesso": True}, 200

def buscar(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario:
        return {"dados": usuario, "sucesso": True}, 200
    return {"erro": "Usuário não encontrado"}, 404

def criar(dados):
    if not dados:
        return {"erro": "Dados inválidos"}, 400
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        return {"erro": "Nome, email e senha são obrigatórios"}, 400
    usuario_id = usuario_model.criar(nome, email, senha)
    print(f"Usuário criado: {email}")
    return {"dados": {"id": usuario_id}, "sucesso": True}, 201

def login(dados):
    dados = dados or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return {"erro": "Email e senha são obrigatórios"}, 400
    usuario = usuario_model.autenticar(email, senha)
    if usuario:
        print(f"Login bem-sucedido: {email}")
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
    print(f"Login falhou: {email}")
    return {"erro": "Email ou senha inválidos", "sucesso": False}, 401
