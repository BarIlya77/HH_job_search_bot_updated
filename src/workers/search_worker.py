import asyncio
import time
from src.services.vacancy_searcher import search_new_vacancies
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


async def search_worker():
    """Воркер для периодического поиска вакансий"""
    logger.info("🔍 Запуск поискового воркера...")

    search_count = 0

    while True:
        try:
            search_count += 1
            logger.info(f"🎯 Запуск поиска #{search_count}...")

            result = await search_new_vacancies()

            if result.get('success'):
                stats = result.get('stats', {})
                logger.info(
                    f"✅ Поиск #{search_count} завершен. Найдено: {stats.get('total_found', 0)}, Новых: {stats.get('new_saved', 0)}")
            else:
                logger.error(f"❌ Ошибка поиска #{search_count}: {result.get('message', 'Unknown error')}")

        except Exception as e:
            logger.error(f"❌ Ошибка в поисковом воркере #{search_count}: {e}")

        # Ждем перед следующим поиском
        interval_minutes = getattr(settings, 'SEARCH_INTERVAL_MINUTES', 30)
        logger.info(f"⏰ Следующий поиск через {interval_minutes} минут...")
        await asyncio.sleep(interval_minutes * 60)


async def main():
    await search_worker()


if __name__ == "__main__":
    asyncio.run(main())
