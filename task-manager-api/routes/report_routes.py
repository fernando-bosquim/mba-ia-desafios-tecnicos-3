from flask import Blueprint, jsonify, request

from controllers import report_controller

report_bp = Blueprint("reports", __name__)

def _resposta(resultado):
    body, status = resultado
    return jsonify(body), status

@report_bp.route("/reports/summary", methods=["GET"])
def summary_report():
    return _resposta(report_controller.summary())

@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id):
    return _resposta(report_controller.user_report(user_id))

@report_bp.route("/categories", methods=["GET"])
def get_categories():
    return _resposta(report_controller.list_categories())

@report_bp.route("/categories", methods=["POST"])
def create_category():
    return _resposta(report_controller.create_category(request.get_json(silent=True)))

@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    return _resposta(report_controller.update_category(cat_id, request.get_json(silent=True)))

@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    return _resposta(report_controller.delete_category(cat_id))
