from flask import Blueprint, jsonify, request
from controllers import user_controller
from middlewares.auth import extract_token_payload, require_roles

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def get_users():
    body, status = user_controller.list_users()
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    body, status = user_controller.get_user_by_id(user_id)
    return jsonify(body), status


@user_bp.route("/users", methods=["POST"])
def create_user():
    current_user, _ = extract_token_payload()
    body, status = user_controller.create_user(
        request.get_json(silent=True),
        current_user=current_user,
    )
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    current_user, auth_error = extract_token_payload()
    body, status = user_controller.update_user(
        user_id,
        request.get_json(silent=True),
        current_user=current_user,
        auth_error=auth_error,
    )
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_roles("admin")
def delete_user(user_id):
    body, status = user_controller.delete_user(user_id)
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    body, status = user_controller.get_user_tasks(user_id)
    return jsonify(body), status


@user_bp.route("/login", methods=["POST"])
def login():
    body, status = user_controller.authenticate_user(request.get_json(silent=True))
    return jsonify(body), status
