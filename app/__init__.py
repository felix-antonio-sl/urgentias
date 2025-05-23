# app/__init__.py
from flask import Flask
from config.config import DevelopmentConfig
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Importar las extensiones
from .extensions import db, migrate, login_manager, csrf

# Definición del filtro nl2br
from markupsafe import Markup, escape

def nl2br(value):
    return Markup("<br>".join(escape(value).split("\n")))

# Importar modelos después de definir las extensiones
# Pero no los importamos aquí para evitar importaciones circulares

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicialización de las extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Registrar el filtro nl2br
    app.jinja_env.filters["nl2br"] = nl2br

    # Registrar los blueprints
    from .routes.main import main as main_bp
    app.register_blueprint(main_bp)

    from .routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    # Registrar manejadores de errores
    from .routes.main import register_error_handlers
    register_error_handlers(app)

    # Configuración de logging
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
        """Agrega el año actual al contexto de las plantillas."""
        return {"current_year": datetime.now().year}

    return app
