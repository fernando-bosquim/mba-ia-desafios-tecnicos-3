from flask import Blueprint, g, jsonify, request

from controllers import task_controller
from middlewares.auth import require_auth

task_bp = Blueprint("tasks", __name__)


def _resposta(resultado):
    body, status = resultado
    return jsonify(body), status


@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    return _resposta(task_controller.list_tasks())


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    return _resposta(task_controller.get_task(task_id))


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    return _resposta(task_controller.create_task(request.get_json(silent=True)))


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    return _resposta(task_controller.update_task(task_id, request.get_json(silent=True)))


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_auth
def delete_task(task_id):
    return _resposta(task_controller.delete_task(task_id, g.current_user))


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    return _resposta(task_controller.search_tasks({
        "q": request.args.get("q", ""),
        "status": request.args.get("status", ""),
        "priority": request.args.get("priority", ""),
        "user_id": request.args.get("user_id", ""),
    }))


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    return _resposta(task_controller.task_stats())
