from werkzeug.security import check_password_hash, generate_password_hash
from models.database import get_db


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def _verificar_senha(senha_armazenada, senha_informada):
    if not senha_armazenada:
        return False, False
    if ":" in senha_armazenada:
        try:
            if check_password_hash(senha_armazenada, senha_informada):
                return True, False
        except ValueError:
            pass
    if senha_armazenada == senha_informada:
        return True, True
    return False, False


def listar_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_row_to_dict(row) for row in cursor.fetchall()]


def buscar_por_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
        (usuario_id,),
    )
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def autenticar(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    valida, precisa_upgrade = _verificar_senha(row["senha"], senha)
    if not valida:
        return None

    if precisa_upgrade:
        novo_hash = generate_password_hash(senha)
        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (novo_hash, row["id"]),
        )
        db.commit()

    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
    }


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid
