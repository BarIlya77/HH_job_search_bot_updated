# scripts/test_db_connection.py
# !/usr/bin/env python3
"""
Простой тест подключения к БД
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import get_logger
from src.core.models import Vacancy, Base
from src.core.database import db as sqlite_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

logger = get_logger(__name__)


async def test_sqlite():
    """Тестирует подключение к SQLite"""
    # sqlite_path = Path("vacancies.db")
    # logger.info(f"Ищем БД: {sqlite_path.absolute()}")
    # logger.info(f"Существует: {sqlite_path.exists()}")
    sqlite_vacancies = await sqlite_db.get_all_vacancies()

    if sqlite_vacancies:
        sqlite_url = f"sqlite+aiosqlite:///{sqlite_path}"
        engine = create_async_engine(sqlite_url, echo=True)

        try:
            async with AsyncSession(engine) as session:
                result = await session.execute(select(Vacancy))
                vacancies = result.scalars().all()
                logger.info(f"Найдено вакансий: {len(vacancies)}")
                for v in vacancies[:3]:
                    logger.info(f"   - {v.name} ({v.company})")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            await engine.dispose()
    else:
        logger.error("Файл БД не найден!")


if __name__ == "__main__":
    asyncio.run(test_sqlite())
