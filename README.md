# Пользовательская аутентификация и управление

## Назначение проекта

Проект предназначен для реализации системы регистрации и аутентификации пользователей с использованием JWT (JSON Web Tokens). Он предоставляет RESTful API для управления пользователями, включая возможность регистрации, авторизации и обновления информации о пользователях. Проект также использует кэширование с помощью Redis для оптимизации работы с токенами и задачами.

## Системные требования

- **Язык**: Python 3.8 или выше
- **Ресурсы**:
  - CPU: 1 GHz или выше
  - RAM: 2 GB или выше
  - Дисковое пространство: 100 MB свободно
- **Системные зависимости**:
  - База данных: PostgreSQL 12 или выше
  - Redis 6 или выше
- **Необходимые расширения**:
  - `uvicorn`
  - `fastapi`
  - `sqlalchemy`
  - `passlib`
  - `python-jose`
  - `pydantic`
  - `asyncpg`
  - `aiocache`
  - `redis`
  
  Установить зависимости можно с помощью `pip install -r requirements.txt`.

## Шаги по установке, сборке, запуску

1. **Клонирование репозитория**:
   ```bash
   git clone https://github.com/username/project.git
   cd project
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
```

5. **Инициализация базы данных: Убедитесь, что PostgreSQL и Redis запущены, затем инициализируйте базу данных, выполнив команду**:
```bash
python -m main 
```

6. **Запуск приложения: Запустите приложение с помощью Uvicorn**:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

7. **Доступ к API**: После запуска приложение будет доступно по адресу http://localhost:8000. 
Перейдите по этому адресу для доступа к автоматически сгенерированной документации API (Swagger UI):
http://localhost:8000/docs