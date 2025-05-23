from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/auth")

templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("login_simple.html", {"request": request})


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # Autenticación simplificada
    return RedirectResponse("/", status_code=302)


@router.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register_simple.html", {"request": request})


@router.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...)):
    # Registro simplificado
    return RedirectResponse("/auth/login", status_code=302)


@router.get("/logout")
async def logout():
    return RedirectResponse("/", status_code=302)
