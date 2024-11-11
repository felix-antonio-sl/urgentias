# app/__init__.py
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
from markupsafe import Markup, escape
from datetime import datetime, timezone


# Definición del filtro nl2br
def nl2br(value):
    return Markup("<br>".join(escape(value).split("\n")))


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

    # Configuración para aceptar tokens CSRF en los encabezados
    app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken"]

    # Inicialización de ell
    ell.init(
        store="./ell_storage",
        autocommit=True,
        verbose=True,
        lazy_versioning=True,
        default_api_params={"temperature": 0.0},
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    csrf.init_app(app)

    # Registrar el filtro nl2br
    app.jinja_env.filters["nl2br"] = nl2br

    from .routes.main import main as main_bp

    app.register_blueprint(main_bp)

    from .routes.auth import auth as auth_bp

    app.register_blueprint(auth_bp)

    from .routes.main import register_error_handlers

    register_error_handlers(app)

    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/urgentias.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Urgentias startup")

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now(timezone.utc).year}

    return app
