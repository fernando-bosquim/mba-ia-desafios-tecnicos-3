import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException
from database import db

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        db.session.rollback()
        logger.exception("Unhandled application error: %s", error)
        return jsonify({"error": "Erro interno"}), 500
