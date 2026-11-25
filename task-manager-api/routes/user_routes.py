from flask import Blueprint, jsonify, request

from controllers import user_controller
from middlewares.auth import get_optional_current_user, require_roles

user_bp = Blueprint("users", __name__)


def _resposta(resultado):
    body, status = resultado
    return jsonify(body), status


@user_bp.route("/users", methods=["GET"])
def get_users():
    return _resposta(user_controller.list_users())


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return _resposta(user_controller.get_user(user_id))


@user_bp.route("/users", methods=["POST"])
def create_user():
    return _resposta(
        user_controller.create_user(request.get_json(silent=True), get_optional_current_user())
    )


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    return _resposta(
        user_controller.update_user(user_id, request.get_json(silent=True), get_optional_current_user())
    )


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_roles("admin")
def delete_user(user_id):
    return _resposta(user_controller.delete_user(user_id))


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    return _resposta(user_controller.user_tasks(user_id))


@user_bp.route("/login", methods=["POST"])
def login():
    return _resposta(user_controller.login(request.get_json(silent=True)))
