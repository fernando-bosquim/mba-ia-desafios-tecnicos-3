from flask import Blueprint, jsonify
from controllers import report_controller
from middlewares.auth import require_roles

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
@require_roles("admin", "manager")
def summary_report():
    body, status = report_controller.get_summary_report()
    return jsonify(body), status


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
@require_roles("admin", "manager")
def user_report(user_id):
    body, status = report_controller.get_user_report(user_id)
    return jsonify(body), status
