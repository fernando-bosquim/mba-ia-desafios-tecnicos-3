from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handler(app):
    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("unhandled")
        return jsonify({"erro": "Erro interno"}), 500
