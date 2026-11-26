from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({"erro": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        current_app.logger.exception("Erro inesperado: %s", error)
        return jsonify({"erro": "Erro interno"}), 500
