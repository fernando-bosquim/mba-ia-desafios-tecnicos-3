from flask import Flask
from flask_cors import CORS
from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from utils.helpers import utc_now


def create_app(config_object=Settings):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_object)

    CORS(flask_app)
    db.init_app(flask_app)

    flask_app.register_blueprint(task_bp)
    flask_app.register_blueprint(user_bp)
    flask_app.register_blueprint(category_bp)
    flask_app.register_blueprint(report_bp)
    register_error_handlers(flask_app)

    @flask_app.route("/health")
    def health():
        return {"status": "ok", "timestamp": str(utc_now())}

    @flask_app.route("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    return flask_app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=app.config["DEBUG"], host=Settings.HOST, port=Settings.PORT)
