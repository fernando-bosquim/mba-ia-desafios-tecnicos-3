from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db

def _publico(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }

def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_publico(row) for row in rows]

def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if row is None:
        return None
    return _publico(row)

def criar(nome, email, senha, tipo="cliente"):
    cursor = get_db().execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    get_db().commit()
    return cursor.lastrowid

def autenticar(email, senha):
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None
    armazenada = row["senha"]
    confere = False
    try:
        confere = check_password_hash(armazenada, senha)
    except (TypeError, ValueError):
        confere = False
    if not confere and armazenada == senha:
        get_db().execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (generate_password_hash(senha), row["id"]),
        )
        get_db().commit()
        confere = True
    if not confere:
        return None
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
    }

def contar():
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
