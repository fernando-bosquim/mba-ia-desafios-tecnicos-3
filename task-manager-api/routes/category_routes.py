from flask import Blueprint, jsonify, request

from controllers import category_controller
from middlewares.auth import require_roles

category_bp = Blueprint("categories", __name__)


def _resposta(resultado):
    body, status = resultado
    return jsonify(body), status


@category_bp.route("/categories", methods=["GET"])
def get_categories():
    return _resposta(category_controller.list_categories())


@category_bp.route("/categories", methods=["POST"])
def create_category():
    return _resposta(category_controller.create_category(request.get_json(silent=True)))


@category_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    return _resposta(category_controller.update_category(cat_id, request.get_json(silent=True)))


@category_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
@require_roles("admin", "manager")
def delete_category(cat_id):
    return _resposta(category_controller.delete_category(cat_id))
