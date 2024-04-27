# Нужные библиотеки
import uvicorn
from fastapi import FastAPI, status, Request
import databases
import sqlalchemy
from sqlalchemy import select
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Определяем URL подключения к базе данных
DATABASE_URL = "sqlite:///./user.db"

# Создаем объект базы данных
database = databases.Database(DATABASE_URL)

# Определяем метаданные
metadata = sqlalchemy.MetaData()

# Определяем таблицу пользователей
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("login", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("age", sqlalchemy.Integer),
    sqlalchemy.Column("height", sqlalchemy.Integer),
)

# Создаем движок базы данных
engine = sqlalchemy.create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

# Экземпляр FastAPI
app = FastAPI(lifespan=lifespan)

# Создаем экземпляр класса для работы с шаблонами
templates = Jinja2Templates(directory="./templates")

# Модели входных и выходных данных
class UserIn(BaseModel):
    login: str
    password: str
    name: str
    age: int
    height: int

class User(BaseModel):
    id: int
    login: str
    password: str
    name: str
    age: int
    height: int

# Создание пользователя
@app.post("/sign_up/", response_model=User)
async def create_user(user: UserIn):
    query = users.insert().values(login=user.login, password=user.password, name=user.name,
                                   age=user.age, height=user.height)
    last_id = await database.execute(query)
    return JSONResponse( {"id": last_id}, status_code=status.HTTP_201_CREATED)

# Вход в аккаунт пользователя
@app.post("/sign_in/")
async def authoriz_user(request: Request, login: str, password: str):
    query = select(users).where(users.c.login == login).where(users.c.password == password)
    user_data = await database.fetch_one(query)
    # Пользователь не найден
    if user_data == None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Пользователь не найден"})
    # Пользователь найден
    user = [
        ("Логин", user_data[1]),
        ("Возраст", user_data[4]),
        ("Рост", user_data[5])
    ]
    context = {"request": request, "user": user}
    return templates.TemplateResponse(
        "log.html", context
    )

# Стартовая страница
@app.get('/', response_class = HTMLResponse)
def index():
    return "<b> Привет, пользователь! </b>" 

# Запуск сервера приложения FastAPI
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)