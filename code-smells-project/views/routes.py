from flask import Blueprint, jsonify, request

from controllers import pedido_controller, produto_controller, sistema_controller, usuario_controller

bp = Blueprint("api", __name__)

def _resposta(resultado):
    body, status = resultado
    return jsonify(body), status

@bp.route("/produtos", methods=["GET"])
def listar_produtos():
    return _resposta(produto_controller.listar())

@bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    return _resposta(produto_controller.buscar_filtros(
        request.args.get("q", ""),
        request.args.get("categoria"),
        request.args.get("preco_min"),
        request.args.get("preco_max"),
    ))

@bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    return _resposta(produto_controller.buscar(produto_id))

@bp.route("/produtos", methods=["POST"])
def criar_produto():
    return _resposta(produto_controller.criar(request.get_json(silent=True)))

@bp.route("/produtos/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    return _resposta(produto_controller.atualizar(produto_id, request.get_json(silent=True)))

@bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
def deletar_produto(produto_id):
    return _resposta(produto_controller.deletar(produto_id))

@bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return _resposta(usuario_controller.listar())

@bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    return _resposta(usuario_controller.buscar(usuario_id))

@bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    return _resposta(usuario_controller.criar(request.get_json(silent=True)))

@bp.route("/login", methods=["POST"])
def login():
    return _resposta(usuario_controller.login(request.get_json(silent=True)))

@bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    return _resposta(pedido_controller.criar(request.get_json(silent=True)))

@bp.route("/pedidos", methods=["GET"])
def listar_pedidos():
    return _resposta(pedido_controller.listar())

@bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    return _resposta(pedido_controller.listar_por_usuario(usuario_id))

@bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    return _resposta(pedido_controller.atualizar_status(pedido_id, request.get_json(silent=True)))

@bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    return _resposta(pedido_controller.relatorio())

@bp.route("/health", methods=["GET"])
def health():
    return _resposta(sistema_controller.health())

@bp.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })

@bp.route("/admin/reset-db", methods=["POST"])
def reset_database():
    return _resposta(sistema_controller.resetar())

@bp.route("/admin/query", methods=["POST"])
def executar_query():
    return _resposta(sistema_controller.recusar_sql(request.get_json(silent=True)))
