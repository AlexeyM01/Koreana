"""
main.py
Основной файл приложения FastAPI
"""
import logging
from fastapi import FastAPI, WebSocket, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from app.models.models import User as UserModel
from app.core.database import init_db, get_db
from app.api.auth import router as auth_router
from app.api.translate import router as translate_router
from app.core.logger import configure_logging
from app.api.roles import router as role_router
from app.core.rate_limiter import limiter, init_rate_limiter


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response


configure_logging()

app = FastAPI()

init_rate_limiter(app)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)


app.include_router(auth_router)
app.include_router(translate_router)
app.include_router(role_router)

logger = logging.getLogger("app")


@app.on_event("startup")
async def startup_event():
    """Функция, выполняемая при запуске приложения fastapi"""
    try:
        await init_db()
        logger.info("Приложение запущено, инициализация базы данных завершена.")
    except Exception as e:
        logger.critical(f"Ошибка при запуске приложения: {e}")


@app.get("/db-status")
@limiter.limit("5/minute")
async def check_db_connection(request: Request, db: AsyncSession = Depends(get_db)):
    """Функция-проверка соединения с базой данных"""
    try:
        await db.execute(select(UserModel).limit(1))
        logger.info("Соединение с базой данных успешно проверено.")
        return HTMLResponse(status_code=200, content="Соединение с базой данных успешно")
    except Exception as e:
        logger.error(f"Ошибка соединения с базой данных: {e}")
        return HTMLResponse(status_code=500, content=f"Соединение с базой данных разорвано. Произошла ошибка {e}")


@app.websocket("/ws/tasks/")
async def websocket_endpoint(websocket: WebSocket):
    """Обрабатывает веб-сокет соединение для взаимодействия с клиентом"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Текст сообщения: {data}")
            logger.debug(f"Получено сообщение по WebSocket: {data}")
    except Exception as e:
        logger.exception(f"Ошибка вебсокета: {e}")
    finally:
        await websocket.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации запроса (например, неверный тип данных)."""
    logger.warning(f"Ошибка валидации запроса: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Общий обработчик исключений.  Логирует ошибку и возвращает стандартный ответ."""
    logger.exception(f"Произошла необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Произошла внутренняя ошибка сервера."},
    )
