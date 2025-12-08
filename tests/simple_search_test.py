"""
Простой тест поиска без pytest
"""

import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import settings
from src.services.vacancy_searcher import search_new_vacancies
from src.core.database import db
from src.core.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Простой тест поиска"""
    logger.info("ТЕСТ ПОИСКА С PARAMETRAMI ИЗ CONFIG")
    logger.info("=" * 50)

    # Показываем параметры
    logger.info(f"Параметры из config:")
    logger.info(f"  SEARCH_QUERY: {settings.SEARCH_QUERY}")
    logger.info(f"  SEARCH_AREAS: {settings.SEARCH_AREAS}")
    logger.info(f"  SEARCH_PER_PAGE: {settings.SEARCH_PER_PAGE}")

    # Инициализация БД
    await db.create_tables()

    # Запускаем поиск
    result = await search_new_vacancies()

    if result['success']:
        stats = result['stats']
        logger.info("ПОИСК УСПЕШЕН!")
        logger.info(f"Результаты:")
        logger.info(f"  Найдено: {stats.get('total_found', 0)}")
        logger.info(f"  Сохранено: {stats.get('new_saved', 0)}")
        logger.info(f"  Дубликатов: {stats.get('duplicates', 0)}")
    else:
        logger.error(f"ПОИСК НЕ УДАЛСЯ: {result.get('message', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())