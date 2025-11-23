from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from src.core.models import Base, Vacancy
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL, echo=True)
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self):
        """Создает таблицы при первом запуске"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Таблицы БД созданы")

    async def save_vacancy(self, vacancy_data):
        """Сохраняет вакансию если её ещё нет"""
        async with self.async_session() as session:
            try:
                # Проверяем есть ли уже такая вакансия
                result = await session.execute(
                    select(Vacancy).where(Vacancy.hh_id == vacancy_data['hh_id'])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    logger.info(f"⏩ Дубликат: {vacancy_data['name']}")
                    return None

                # Создаем новую вакансию
                vacancy = Vacancy(**vacancy_data)
                session.add(vacancy)
                await session.commit()
                await session.refresh(vacancy)
                logger.info(f"✅ Новая: {vacancy_data['name']}")
                return vacancy

            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Ошибка сохранения: {e}")
                return None

    async def get_vacancy_by_hh_id(self, hh_id):
        """Получает вакансию по HH ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Vacancy).where(Vacancy.hh_id == hh_id)
            )
            return result.scalar_one_or_none()

    async def mark_cover_letter_generated(self, vacancy_id, cover_letter_text):
        """Помечает что письмо сгенерировано и сохраняет текст"""
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(Vacancy).where(Vacancy.id == vacancy_id)
                )
                vacancy = result.scalar_one_or_none()

                if vacancy:
                    vacancy.processed = True
                    vacancy.cover_letter_generated = True
                    vacancy.cover_letter = cover_letter_text
                    vacancy.cover_letter_generated_at = datetime.utcnow()
                    await session.commit()
                    logger.info(f"✅ Письмо сохранено для ID: {vacancy_id}")
                    return True
                else:
                    logger.error(f"❌ Вакансия не найдена: {vacancy_id}")
                    return False
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Ошибка сохранения письма: {e}")
                return False

    async def get_unprocessed_vacancies(self):
        """Получает непроцессированные вакансии"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Vacancy).where(Vacancy.processed == False)
            )
            return result.scalars().all()

    async def get_vacancies_with_cover_letters(self):
        """Получает вакансии с сгенерированными письмами"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Vacancy).where(Vacancy.cover_letter_generated == True)
            )
            return result.scalars().all()

    async def get_all_vacancies(self):
        """Получает все вакансии"""
        async with self.async_session() as session:
            result = await session.execute(select(Vacancy))
            return result.scalars().all()

    async def mark_as_applied(self, vacancy_id):
        """Помечает вакансию как отправленную"""
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(Vacancy).where(Vacancy.id == vacancy_id)
                )
                vacancy = result.scalar_one_or_none()

                if vacancy:
                    vacancy.applied = True
                    vacancy.applied_at = datetime.utcnow()
                    await session.commit()
                    logger.info(f"✅ Отправлена: {vacancy.name}")
                    return True
                return False
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Ошибка отметки отправки: {e}")
                return False


# Глобальный экземпляр
db = Database()
