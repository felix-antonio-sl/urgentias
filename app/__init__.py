# app/__init__.py
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from pathlib import Path
from markupsafe import Markup, escape


def nl2br(value):
    return Markup("<br>".join(escape(value).split("\n")))


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["nl2br"] = nl2br


def create_app() -> FastAPI:
    """Construye y devuelve la instancia principal de FastAPI."""
    app = FastAPI()

    from .routes.main import router as main_router
    from .routes.auth import router as auth_router

    app.include_router(main_router)
    app.include_router(auth_router)

    return app
