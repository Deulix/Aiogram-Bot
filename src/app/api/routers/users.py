import hashlib
import uuid

from fastapi import HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: F401
from fastapi.routing import APIRouter
from pydantic import BaseModel, model_validator

user_router = APIRouter(prefix="/users")


class User(BaseModel):
    id: uuid.UUID
    username: str
    password_hashed: str


db: dict[str, User] = {}


######### REGISTER #########


class UserRegisterInput(BaseModel):
    username: str
    password: str
    password_confirm: str

    @model_validator(mode="after")
    def passwords_check(self):
        if self.password != self.password_confirm:
            raise ValueError("passwords are not the same")
        return self


class UserRegisterResponse(BaseModel):
    id: uuid.UUID | None = None
    username: str
    registered: bool


######### LOGIN #########


class UserLoginInput(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    id: uuid.UUID
    username: str
    logged_in: bool


@user_router.post("/register", tags=["Users"], response_model=UserRegisterResponse)
async def register_user(user: UserRegisterInput):
    if user.username not in db:
        user_id = uuid.uuid5(namespace=uuid.NAMESPACE_DNS, name=user.username)
        password_hashed = hashlib.sha256(user.password.encode()).hexdigest()
        db_user = User(
            id=user_id, username=user.username, password_hashed=password_hashed
        )
        db[user.username] = db_user

    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "user registered already")

    return UserRegisterResponse(id=db_user.id, username=user.username, registered=True)


@user_router.post("/login", tags=["Users"], response_model=UserLoginResponse)
async def login(user: UserLoginInput):
    if user.username not in db:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user is not registered")

    elif (
        hashlib.sha256(user.password.encode()).hexdigest()
        != db[user.username].password_hashed
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong password")

    db_user = db[user.username]

    return UserLoginResponse(id=db_user.id, username=user.username, logged_in=True)
