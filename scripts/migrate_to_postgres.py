# scripts/migrate_to_postgres.py
#!/usr/bin/env python3
"""
Простая миграция из SQLite в PostgreSQL
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import get_logger
from src.core.config import settings
from src.core.models import Vacancy, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = get_logger(__name__)

async def get_sqlite_vacancies():
    """Получает вакансии из существующей SQLite БД"""
    
    # Используем существующий SQLite файл
    sqlite_path = Path("vacancies.db")
    if not sqlite_path.exists():
        logger.error(f"Файл БД не найден: {sqlite_path}")
        return []
    
    # Создаем движок для существующей SQLite БД
    sqlite_url = f"sqlite+aiosqlite:///{sqlite_path}"
    sqlite_engine = create_async_engine(sqlite_url, echo=True)
    sqlite_session = sessionmaker(
        sqlite_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        # Получаем все вакансии
        async with sqlite_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Vacancy))
            vacancies = result.scalars().all()
            logger.info(f"📦 Найдено вакансий в SQLite: {len(vacancies)}")
            return vacancies
            
    except Exception as e:
        logger.error(f"Ошибка чтения SQLite: {e}")
        return []
    finally:
        await sqlite_engine.dispose()

async def migrate_to_postgres(postgres_url: str):
    """Переносит данные из SQLite в PostgreSQL"""
    
    # Получаем данные из SQLite
    sqlite_vacancies = await get_sqlite_vacancies()
    
    if not sqlite_vacancies:
        logger.error("Нет данных для миграции")
        return
    
    # Подключаемся к PostgreSQL
    postgres_engine = create_async_engine(postgres_url, echo=True)
    postgres_session = sessionmaker(
        postgres_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        # Создаем таблицы в PostgreSQL
        async with postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Переносим данные
        async with postgres_session() as session:
            migrated_count = 0
            for vacancy in sqlite_vacancies:
                try:
                    # Создаем новую запись в PostgreSQL
                    new_vacancy = Vacancy(
                        hh_id=vacancy.hh_id,
                        name=vacancy.name,
                        company=vacancy.company,
                        salary_from=vacancy.salary_from,
                        salary_to=vacancy.salary_to,
                        salary_currency=vacancy.salary_currency,
                        experience=vacancy.experience,
                        employment=vacancy.employment,
                        description=vacancy.description,
                        skills=vacancy.skills,
                        url=vacancy.url,
                        processed=vacancy.processed,
                        cover_letter_generated=vacancy.cover_letter_generated,
                        cover_letter=vacancy.cover_letter,
                        cover_letter_generated_at=vacancy.cover_letter_generated_at,
                        applied=vacancy.applied,
                        applied_at=vacancy.applied_at,
                        created_at=vacancy.created_at
                    )
                    session.add(new_vacancy)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка миграции вакансии {vacancy.hh_id}: {e}")
            
            await session.commit()
            logger.info(f"Перенесено в PostgreSQL: {migrated_count} вакансий")
            
    except Exception as e:
        logger.error(f"Ошибка миграции: {e}")
    finally:
        await postgres_engine.dispose()

async def main():
    if len(sys.argv) != 2:
        print("Использование: python scripts/migrate_to_postgres.py postgresql+asyncpg://user:password@localhost/dbname")
        print("Пример: python scripts/migrate_to_postgres.py postgresql+asyncpg://postgres:password@localhost:5432/hh_bot")
        return
    
    postgres_url = sys.argv[1]
    await migrate_to_postgres(postgres_url)

if __name__ == "__main__":
    asyncio.run(main())