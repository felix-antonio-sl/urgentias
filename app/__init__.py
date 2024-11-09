from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.config import DevelopmentConfig
import logging
from logging.handlers import RotatingFileHandler
import os
import ell
from flask_wtf import CSRFProtect
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

from .models import User, Paciente, Atencion

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    ell.init(store='./logdir', verbose=True, autocommit=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    csrf.init_app(app)

    from .routes.main import main as main_bp
    app.register_blueprint(main_bp)

    from .routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from .routes.main import register_error_handlers
    register_error_handlers(app)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/urgentias.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Urgentias startup')

    return app
