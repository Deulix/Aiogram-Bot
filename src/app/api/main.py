from fastapi import FastAPI, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.app.api.services import user_service as us
from src.app.database.sqlite_db import AsyncSQLiteDatabase

app = FastAPI(title="Админпанель пиццерии")

templates = Jinja2Templates(directory="src/app/api/templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request,
            "title": "Главная",
        },
    )


class UserResponse(BaseModel):
    id: int
    name: str


@app.get("/user", response_model=list[UserResponse])
async def api_get_users():
    users = await us.get_users(AsyncSQLiteDatabase)
    return users


@app.get("/user/{user_id}", response_model=UserResponse)
async def api_get_user_by_id(user_id: int):
    user = await us.get_user_by_id(AsyncSQLiteDatabase, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с id {user_id} не найден",
        )
    return user


# @app.get("/requests")
# def get_my_requests(request: Request):
#     user_ip_address = request.client.host
#     print(f"{user_ip_address = }")
#     user_requests = get_user_requests(ip_address=user_ip_address)
#     return user_requests


# @app.post("/requests")
# def send_prompt(request: Request, prompt: str = Body(embed=True)):
#     response = get_answer_from_gemini(prompt)
#     user_ip_address = request.client.host
#     add_request_data(ip_address=user_ip_address, prompt=prompt, response=response)
#     return {"response": response}
