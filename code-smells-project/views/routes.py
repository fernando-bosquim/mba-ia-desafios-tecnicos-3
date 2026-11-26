from flask import Blueprint, jsonify, request
from controllers import (
    admin_controller,
    pedido_controller,
    produto_controller,
    relatorio_controller,
    usuario_controller,
)
from middlewares.auth import extrair_usuario_opcional, require_roles

api_bp = Blueprint("api", __name__)


def _respond(result):
    body, status = result
    return jsonify(body), status


@api_bp.route("/", methods=["GET"])
def index():
    return _respond(admin_controller.index())


@api_bp.route("/health", methods=["GET"])
def health_check():
    return _respond(admin_controller.health_check())


@api_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    return _respond(produto_controller.listar_produtos())


@api_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    return _respond(
        produto_controller.buscar_produtos(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=request.args.get("preco_min"),
            preco_max=request.args.get("preco_max"),
        )
    )


@api_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    return _respond(produto_controller.buscar_produto(produto_id))


@api_bp.route("/produtos", methods=["POST"])
def criar_produto():
    return _respond(produto_controller.criar_produto(request.get_json(silent=True)))


@api_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    return _respond(
        produto_controller.atualizar_produto(produto_id, request.get_json(silent=True))
    )


@api_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
@require_roles("admin")
def deletar_produto(produto_id):
    return _respond(produto_controller.deletar_produto(produto_id))


@api_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return _respond(usuario_controller.listar_usuarios())


@api_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    return _respond(usuario_controller.buscar_usuario(usuario_id))


@api_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    return _respond(
        usuario_controller.criar_usuario(
            request.get_json(silent=True),
            usuario_autenticado=extrair_usuario_opcional(),
        )
    )


@api_bp.route("/login", methods=["POST"])
def login():
    return _respond(usuario_controller.login(request.get_json(silent=True)))


@api_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    return _respond(pedido_controller.criar_pedido(request.get_json(silent=True)))


@api_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    return _respond(pedido_controller.listar_todos_pedidos())


@api_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    return _respond(pedido_controller.listar_pedidos_usuario(usuario_id))


@api_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    return _respond(
        pedido_controller.atualizar_status_pedido(pedido_id, request.get_json(silent=True))
    )


@api_bp.route("/relatorios/vendas", methods=["GET"])
@require_roles("admin")
def relatorio_vendas():
    return _respond(relatorio_controller.relatorio_vendas())


@api_bp.route("/admin/reset-db", methods=["POST"])
@require_roles("admin")
def reset_database():
    return _respond(admin_controller.reset_database())


@api_bp.route("/admin/query", methods=["POST"])
@require_roles("admin")
def executar_query():
    return _respond(admin_controller.executar_query())
