# scripts/clean_database.py
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import db
from src.core.logger import get_logger

logger = get_logger(__name__)


async def clean_database():
    """Полностью очищает БД"""
    await db.create_tables()

    async with db.async_session() as session:
        # Удаляем ВСЕ вакансии
        from src.core.models import Vacancy
        result = await session.execute("DELETE FROM vacancies")
        await session.commit()
        logger.info(f"🗑️ Удалено вакансий: {result.rowcount}")


if __name__ == "__main__":
    asyncio.run(clean_database())
