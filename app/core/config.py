"""
app/core/config.py
Определяет настройки приложения с использованием Pydantic.
Настройки включают секретные ключи, конфигурацию базы данных и Redis.
Загружает переменные окружения из файла .env.
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    """
    Класс для определения и хранения конфигурационных настроек приложения.

    Атрибуты:
        secret_key (str): Секретный ключ для JWT.
        algorithm (str): Алгоритм шифрования для токенов.
        access_token_expire_minutes (int): Время жизни access токена в минутах.
        refresh_token_expire_minutes (int): Время жизни refresh токена в минутах.
        db_name (str): Имя базы данных.
        db_user (str): Имя пользователя базы данных.
        db_password (str): Пароль пользователя базы данных.
        db_host (str): Хост базы данных.
        db_port (int): Порт базы данных.
        redis_url (str): URL для подключения к Redis.
        smtp_server (str): SMTP сервер для отправки электронной почты.
        email_password (str): Пароль к учетной записи электронной почты.
        email_sender (str): Адрес электронной почты отправителя.
        smtp_port (int): Порт SMTP сервера.
    """
    secret_key: str = os.getenv("SECRET_KEY", "your_secret_key")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    refresh_token_expire_minutes: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 60 * 24 * 30))  # 30 дней

    db_name: str = os.getenv("DB_NAME", "postgres")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "password")
    db_host: str = os.getenv("DB_HOST", "db")
    db_port: int = int(os.getenv("DB_PORT", 5432))

    redis_host: str = os.getenv("REDIS_HOST", "redis://localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))

    yandex_translate_api_key: str = os.getenv("YANDEX_TRANSLATE_API_KEY")
    yandex_translate_folder_id: str = os.getenv("YANDEX_TRANSLATE_FOLDER_ID")

    @property
    def database_url(self) -> str:
        """
        Создает строку подключения к базе данных.
        Returns:
            str: Полная строка подключения к базе данных.
        """
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        """Конфигурация Pydantic для загрузки переменных окружения из файла."""
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
