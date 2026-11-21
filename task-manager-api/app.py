from datetime import datetime

from flask import Flask
from flask_cors import CORS

from config.settings import DATABASE_URI, DEBUG, HOST, PORT, SECRET_KEY
from database import db
from middlewares.error_handler import register_error_handler
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

def create_app():
    application = Flask(__name__)
    application.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    application.config["SECRET_KEY"] = SECRET_KEY
    CORS(application)
    db.init_app(application)
    register_error_handler(application)
    application.register_blueprint(task_bp)
    application.register_blueprint(user_bp)
    application.register_blueprint(report_bp)

    @application.route("/health")
    def health():
        return {"status": "ok", "timestamp": str(datetime.now())}

    @application.route("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    return application

app = create_app()

def init_database():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    init_database()
    app.run(debug=DEBUG, host=HOST, port=PORT)
