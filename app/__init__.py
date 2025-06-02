from flask import Flask
from .extensions import db, mail
from flask_login import LoginManager
from .routes import main 
from dotenv import load_dotenv

login_manager = LoginManager()

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)


    # Import models to register with SQLAlchemy
    with app.app_context():
        from . import models

    # Register blueprints
    from .routes import main
    from .auth import auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    from app.context_processors import base_context
    app.context_processor(base_context)

    return app
