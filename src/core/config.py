# src/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения"""

    # Название приложения
    APP_NAME: str = "HH Job Bot"
    APP_VERSION: str = "2.0.0"

    # 🔐 HH.ru API
    HH_ACCESS_TOKEN: str = os.getenv("HH_ACCESS_TOKEN", "")
    HH_RESUME_ID: str = os.getenv("HH_RESUME_ID", "")
    HH_CLIENT_ID: str = os.getenv("HH_CLIENT_ID", "")
    HH_CLIENT_SECRET: str = os.getenv("HH_CLIENT_SECRET", "")
    HH_API_URL: str = "https://api.hh.ru/vacancies"

    # 🤖 DeepSeek API
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"

    # 🗃️ Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///vacancies.db")

    # 📨 RabbitMQ
    # Подключение к RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    # Названия очередей
    QUEUE_VACANCIES: str = "vacancies_to_process"
    QUEUE_COVER_LETTERS: str = "cover_letters_to_send"

    # ⚡ Rate Limits
    REQUESTS_PER_HOUR: int = 5  # Откликов в час
    SEARCH_REQUESTS_PER_HOUR: int = 10  # Поисковых запросов в час
    MAX_CONCURRENT_REQUESTS: int = 2
    REQUEST_DELAY: float = 0.3

    # 🔍 Search Parameters
    SEARCH_QUERY: str = "Python разработчик OR Python developer OR backend Python"
    SEARCH_AREAS: List[int] = [1, 2, 113]  # Москва, СПб, Россия
    SEARCH_PER_PAGE: int = 20
    SEARCH_INTERVAL: int = 3600  # 1 час

    # 🎯 Keywords для фильтрации Python вакансий
    PYTHON_KEYWORDS: List[str] = [
        'python', 'питон', 'fastapi', 'django', 'flask',
        'backend', 'бэкенд', 'разработчик', 'developer'
    ]

    # 📧 Контакты для писем
    CONTACT_NAME: str = os.getenv("CONTACT_NAME", "")
    CONTACT_TELEGRAM: str = os.getenv("CONTACT_TELEGRAM", "")
    CONTACT_EMAIL: str = os.getenv("CONTACT_EMAIL", "")
    CONTACT_PHONE: str = os.getenv("CONTACT_PHONE", "")
    CONTACT_GITHUB: str = os.getenv("CONTACT_GITHUB", "")

    # 🤖 Режим работы бота
    BOT_MODE: str = os.getenv("BOT_MODE", "automatic")  # automatic или interactive

    # 🎨 Logging
    LOG_LEVEL: str = "INFO"
    COLORED_LOGS: bool = True

    class Config:
        env_file = ".env"


# Глобальный экземпляр настроек
settings = Settings()
