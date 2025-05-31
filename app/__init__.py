from flask import Flask
from .extensions import db 
from flask_login import LoginManager
from .routes import main 

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)

    # Import models to register with SQLAlchemy
    with app.app_context():
        from . import models

    # Register blueprints
    from .routes import main
    from .auth import auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {"now": datetime.utcnow}


    return app
