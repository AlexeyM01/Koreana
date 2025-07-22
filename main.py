"""
main.py
Основной файл приложения FastAPI
"""
from fastapi import FastAPI, WebSocket, Depends
import uvicorn
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from models import User as UserModel
from database import init_db, get_db
from auth import router as auth_router

app = FastAPI()
app.include_router(auth_router)


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
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
        except Exception as e:
            await websocket.close()
            print(f"WebSocket error: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
