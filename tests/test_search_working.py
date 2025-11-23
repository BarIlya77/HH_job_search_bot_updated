"""
Тест с рабочими параметрами поиска
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.logger import get_logger
from src.services.vacancy_searcher import search_new_vacancies
from src.core.database import db

logger = get_logger(__name__)


async def test_with_working_params():
    """Тест с гарантированно рабочими параметрами"""
    logger.info("🎯 ТЕСТ С РАБОЧИМИ ПАРАМЕТРАМИ")
    logger.info("=" * 50)

    # Параметры которые точно должны работать
    working_params = {
        "text": "Python",
        "area": 1,  # Москва
        "per_page": 5,
        "page": 0
    }

    logger.info(f"🔍 Параметры: {working_params}")

    result = await search_new_vacancies(working_params)

    if result.get('success'):
        stats = result.get('stats', {})
        logger.info("✅ ПОИСК РАБОТАЕТ!")
        logger.info(f"📊 Результаты:")
        logger.info(f"   Найдено: {stats.get('total_found', 0)}")
        logger.info(f"   Сохранено: {stats.get('new_saved', 0)}")
        logger.info(f"   Дубликатов: {stats.get('duplicates', 0)}")
        logger.info(f"   В очередь: {stats.get('sent_to_queue', 0)}")

        # Показываем сохраненные вакансии
        vacancies = await db.get_all_vacancies()
        logger.info(f"\n📋 Всего в БД: {len(vacancies)} вакансий")

        for i, vacancy in enumerate(vacancies[-3:]):  # Последние 3
            status = "🆕" if not vacancy.processed else "📝" if vacancy.cover_letter_generated else "⏳"
            logger.info(f"   {status} {vacancy.name} - {vacancy.company}")

        return True
    else:
        logger.error(f"❌ Поиск не удался: {result.get('message', 'Unknown error')}")
        return False


async def test_current_config():
    """Тестируем параметры из config.py"""
    logger.info("\n🔧 ТЕСТ ТЕКУЩИХ ПАРАМЕТРОВ ИЗ CONFIG")
    logger.info("=" * 50)

    from src.core.config import settings

    logger.info(f"Текущие параметры:")
    logger.info(f"  SEARCH_QUERY: {settings.SEARCH_QUERY}")
    logger.info(f"  SEARCH_AREAS: {settings.SEARCH_AREAS}")
    logger.info(f"  SEARCH_PER_PAGE: {settings.SEARCH_PER_PAGE}")

    # Тест с параметрами из config
    result = await search_new_vacancies()

    if result.get('success'):
        logger.info("✅ Параметры из config.py РАБОТАЮТ!")
        return True
    else:
        logger.error("❌ Параметры из config.py НЕ РАБОТАЮТ!")
        logger.info("💡 Нужно исправить SEARCH_QUERY в config.py")
        return False


async def main():
    await db.create_tables()

    # Сначала тест с гарантированными параметрами
    success1 = await test_with_working_params()

    # Затем тест с параметрами из config
    success2 = await test_current_config()

    logger.info("\n" + "=" * 50)
    if success1 and success2:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    elif success1 and not success2:
        logger.info("⚠️  Рабочие параметры есть, но config нужно исправить")
    else:
        logger.error("💥 Есть проблемы с поиском")


if __name__ == "__main__":
    asyncio.run(main())
