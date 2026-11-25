from flask import Blueprint, g, jsonify

from controllers import report_controller
from middlewares.auth import require_auth, require_roles

report_bp = Blueprint("reports", __name__)


def _resposta(resultado):
    body, status = resultado
    return jsonify(body), status


@report_bp.route("/reports/summary", methods=["GET"])
@require_roles("admin", "manager")
def summary_report():
    return _resposta(report_controller.summary())


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
@require_auth
def user_report(user_id):
    return _resposta(report_controller.user_report(user_id, g.current_user))
