"""
main.py
Основной файл приложения FastAPI
"""
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from app.models.models import User as UserModel
from app.core.database import init_db, get_db
from app.api.auth import router as auth_router
from app.api.translate import router as translate_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)
app.include_router(auth_router)
app.include_router(translate_router)


@app.on_event("startup")
async def startup_event():
    """Функция, выполняемая при запуске приложения fastapi"""
    await init_db()


@app.get("/db-status")
async def check_db_connection(db: AsyncSession = Depends(get_db)):
    """Функция-проверка соединения с базой данных"""
    try:
        await db.execute(select(UserModel).limit(1))
        return HTMLResponse(status_code=200, content="Соединение с базой данных успешно")
    except Exception as e:
        return HTMLResponse(status_code=500, content=f"Соединение с базой данных разорвано. Произошла ошибка {e}")


@app.websocket("/ws/tasks/")
async def websocket_endpoint(websocket: WebSocket):
    """Обрабатывает веб-сокет соединение для взаимодействия с клиентом"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Текст сообщения: {data}")
    except Exception as e:
        print(f"Возникла ошибка вебсокета: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
