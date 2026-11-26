import logging
from flask import Flask
from flask_cors import CORS
from config import settings
from middlewares.error_handler import register_error_handlers
from models.database import close_db, init_db
from views.routes import api_bp


def create_app():
    logging.basicConfig(level=logging.INFO)
    application = Flask(__name__)
    application.config["SECRET_KEY"] = settings.SECRET_KEY
    application.config["DEBUG"] = settings.DEBUG
    application.config["DATABASE_PATH"] = settings.DATABASE_PATH
    application.config["TOKEN_MAX_AGE"] = settings.TOKEN_MAX_AGE

    CORS(application)
    application.teardown_appcontext(close_db)
    register_error_handlers(application)
    application.register_blueprint(api_bp)
    return application


app = create_app()


if __name__ == "__main__":
    init_db(app.config["DATABASE_PATH"])
    app.logger.info("Servidor iniciado em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
