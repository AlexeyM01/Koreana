# Пользовательская аутентификация и управление

## Назначение проекта

Это FastAPI проект, реализующий API для аутентификации, управления ролями, перевода текста. Проект использует асинхронную базу данных PostgreSQL, JWT для аутентификации и Redis для ограничения скорости (rate limiting).

## Технологии

•   FastAPI
•   Python 3.11+
•   SQLAlchemy (Async)
•   PostgreSQL
•   JWT
•   Redis
•   Pydantic
•   Passlib
•   requests
•   python-dotenv

## Шаги по установке, сборке, запуску

1. **Клонирование репозитория**:
   ```bash
   git clone https://github.com/AlexeyM01/Koreana.git
   cd Koreana
   ```

2. **Создание и активация виртуального окружения**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Linux и MacOS
   venv\Scripts\activate  # Для Windows
   ```

3. **Установка зависимостей**:
   ```bash
   Copied
   Copy code
   pip install -r requirements.txt
   ```

4. **Настройка переменных окружения: Создайте файл .env в корне проекта и добавьте необходимые переменные**:
```
SECRET_KEY=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
REDIS_URL=

YANDEX_TRANSLATE_API_KEY=
YANDEX_TRANSLATE_FOLDER_ID=
```

5. **Инициализация базы данных: Убедитесь, что PostgreSQL и Redis запущены, затем инициализируйте базу данных, выполнив команду**:
```bash
python -m main 
```

6. **Запуск приложения: Запустите приложение с помощью Uvicorn**:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload --log-level info
```

7. **Доступ к API**: После запуска приложение будет доступно по адресу http://localhost:8000. 
Перейдите по этому адресу для доступа к автоматически сгенерированной документации API (Swagger UI):
http://localhost:8000/docs

8. Эндпоинты API

•  POST /registration/: Регистрация нового пользователя.
•  POST /login/: Аутентификация пользователя и получение JWT токенов.
•  GET /me: Получение информации о текущем пользователе (требуется аутентификация).
•  PUT /me: Обновление информации о текущем пользователе (требуется аутентификация).
•  POST /refresh/: Обновление access token с использованием refresh token.
•  POST /translate/: Перевод текста с использованием Yandex Translate.
•  GET /db-status: Проверка соединения с базой данных.
•  GET /ws/tasks/: WebSocket endpoint для двусторонней связи.

•  POST /roles/: Создание новой роли (требуется аутентификация и права "manage_users").
•  GET /roles/{role_id}: Получение информации о роли по ID (требуется аутентификация и права "manage_users").
•  PUT /roles/{role_id}: Обновление информации о роли по ID (требуется аутентификация и права "manage_users").
•  DELETE /roles/{role_id}: Удаление роли по ID (требуется аутентификация и права "manage_users").