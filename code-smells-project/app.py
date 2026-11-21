from flask import Flask
from flask_cors import CORS

from config.settings import DEBUG, HOST, PORT, SECRET_KEY
from database import close_db, init_db
from middlewares.error_handler import register_error_handler
from views.routes import bp

def create_app():
    application = Flask(__name__)
    application.config["SECRET_KEY"] = SECRET_KEY
    application.config["DEBUG"] = DEBUG
    CORS(application)
    application.teardown_appcontext(close_db)
    register_error_handler(application)
    application.register_blueprint(bp)
    return application

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        init_db()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://{HOST}:{PORT}")
    print("=" * 50)
    app.run(host=HOST, port=PORT, debug=DEBUG)
