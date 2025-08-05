"""
app/core/config.py
Определяет настройки приложения с использованием Pydantic.
Настройки включают секретные ключи, конфигурацию базы данных и Redis.
Загружает переменные окружения из файла .env.
"""
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Класс для определения и хранения конфигурационных настроек приложения.

    Атрибуты:
        secret_key (str): Секретный ключ для JWT.
        algorithm (str): Алгоритм шифрования для токенов.
        access_token_expire_minutes (int): Время жизни токена в минутах.
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
    db_name: str = os.getenv("DB_NAME", "postgres")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "password")
    db_host: str = os.getenv("DB_HOST", "db")
    db_port: int = int(os.getenv("DB_PORT", 5432))

#    redis_url: str = os.getenv("REDIS_HOST", "redis://localhost")
#    redis_password: str = os.getenv("REDIS_PASSWORD", "password")
#    redis_port: int = 6379

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
