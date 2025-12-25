from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: F401
from fastapi.routing import APIRouter
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="src/app/api/templates")


auth_router = APIRouter(tags=["auth"])


@auth_router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        name="login.html",
        context={
            "request": request,
            "title": "Авторизация",
        },
    )


@auth_router.post("/index")
async def index(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request,
            "title": "Главная",
        },
    )
