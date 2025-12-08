# test_search_simple.py
# !/usr/bin/env python3
"""
Упрощенный тест поиска и сохранения вакансий
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import get_logger
from src.api.hh_client import HHClient
from src.core.database import db

logger = get_logger(__name__)


async def simple_search_and_save():
    """Простой поиск и сохранение вакансий"""
    logger.info("ПРОСТОЙ ПОИСК И СОХРАНЕНИЕ")
    logger.info("=" * 50)

    # Инициализация БД
    await db.create_tables()

    # Создаем клиент
    client = HHClient()

    # Простые параметры поиска
    simple_params = {
        "text": "Python разработчик OR Python developer OR backend Python",
        "area": [1, 2, 113],  # Москва
        "per_page": 5,  # Всего 5 вакансий
        "page": 0
    }

    logger.info(f"Параметры поиска: {simple_params}")

    # Поиск вакансий
    search_result = await client.search_vacancies(simple_params)

    if not search_result or not search_result.get('items'):
        logger.error("Не найдено вакансий даже с простыми параметрами!")
        return False

    logger.info(f"Найдено вакансий: {len(search_result['items'])}")

    # Получаем полные данные
    vacancies_data = await client.get_multiple_vacancies_details(search_result['items'])
    logger.info(f"Загружено полных данных: {len(vacancies_data)}")

    # Сохраняем в БД
    saved_count = 0
    for vacancy_data in vacancies_data:
        vacancy = await db.save_vacancy(vacancy_data)
        if vacancy:
            saved_count += 1
            logger.info(f"Сохранено: {vacancy_data['name']}")
        else:
            logger.info(f"Дубликат: {vacancy_data['name']}")

    logger.info(f"\nИТОГИ:")
    logger.info(f"  Найдено: {len(vacancies_data)}")
    logger.info(f"  Сохранено: {saved_count}")
    logger.info(f"  Дубликатов: {len(vacancies_data) - saved_count}")

    # Показываем сохраненные вакансии
    all_vacancies = await db.get_all_vacancies()
    logger.info(f"\nВсего в БД: {len(all_vacancies)} вакансий")

    for i, vacancy in enumerate(all_vacancies[-5:]):  # Последние 5
        status = "new" if not vacancy.processed else "done"
        logger.info(f"  {status} {vacancy.name} - {vacancy.company}")

    return saved_count > 0


async def main():
    success = await simple_search_and_save()

    if success:
        logger.info("\nПОИСК И СОХРАНЕНИЕ РАБОТАЮТ!")
    else:
        logger.error("\nЕСТЬ ПРОБЛЕМЫ С ПОИСКОМ!")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)