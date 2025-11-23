"""
Тест обработки вакансий и генерации писем
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.logger import get_logger
from src.core.database import db
from src.services.vacancy_processor import vacancy_processor
from src.api.deepseek_client import DeepSeekClient

logger = get_logger(__name__)


async def test_deepseek_connection():
    """Тестируем подключение к DeepSeek API"""
    logger.info("🧪 ТЕСТ ПОДКЛЮЧЕНИЯ К DEEPSEEK")
    logger.info("=" * 50)

    client = DeepSeekClient()

    if not client.api_key:
        logger.error("❌ DEEPSEEK_API_KEY не установлен в .env")
        logger.info("💡 Добавь DEEPSEEK_API_KEY=твой_ключ в .env файл")
        return False

    logger.info("✅ DEEPSEEK_API_KEY найден")

    # Тестируем подключение
    if await client.test_connection():
        logger.info("✅ Подключение к DeepSeek API успешно")
        return True
    else:
        logger.error("❌ Ошибка подключения к DeepSeek API")
        return False


async def test_letter_generation():
    """Тестируем генерацию писем для разных вакансий"""
    logger.info("\n🧪 ТЕСТ ГЕНЕРАЦИИ ПИСЕМ")
    logger.info("=" * 50)

    client = DeepSeekClient()

    # Тестовые вакансии
    test_vacancies = [
        {
            'name': 'Python разработчик',
            'company': 'ТехноЛаб',
            'description': 'Ищем Python разработчика с опытом работы с FastAPI и Django. Требуется знание PostgreSQL, Docker.',
            'skills': 'Python, FastAPI, Django, PostgreSQL, Docker',
            'hh_id': 'test_python_1'
        },
        {
            'name': 'Backend Developer (Python)',
            'company': 'DataSoft',
            'description': 'Разработка backend на Python. Работа с микросервисной архитектурой, REST API.',
            'skills': 'Python, FastAPI, REST, микросервисы',
            'hh_id': 'test_python_2'
        },
        {
            'name': 'Java разработчик',  # Не Python - должна быть пропущена
            'company': 'BankSystem',
            'description': 'Разработка на Java, Spring Framework',
            'skills': 'Java, Spring, Hibernate',
            'hh_id': 'test_java_1'
        }
    ]

    for i, vacancy_data in enumerate(test_vacancies, 1):
        logger.info(f"\n🔧 Тест {i}: {vacancy_data['name']}")

        cover_letter = await client.generate_cover_letter(vacancy_data)

        if cover_letter:
            logger.info(f"✅ Письмо сгенерировано ({len(cover_letter)} символов)")
            logger.info(f"📝 Превью: {cover_letter[:100]}...")
        else:
            logger.info("⏩ Пропущено (не Python вакансия)")


async def test_processing_real_vacancies():
    """Тестируем обработку реальных вакансий из БД"""
    logger.info("\n🧪 ТЕСТ ОБРАБОТКИ РЕАЛЬНЫХ ВАКАНСИЙ")
    logger.info("=" * 50)

    # Получаем необработанные вакансии из БД
    unprocessed_vacancies = await db.get_unprocessed_vacancies()

    if not unprocessed_vacancies:
        logger.info("📭 Нет необработанных вакансий в БД")
        logger.info("💡 Сначала запусти поиск: python test_search_simple.py")
        return False

    logger.info(f"📋 Найдено необработанных вакансий: {len(unprocessed_vacancies)}")

    # Обрабатываем первые 2 вакансии
    processed_count = 0
    for i, vacancy in enumerate(unprocessed_vacancies[:2]):
        logger.info(f"\n🔧 Обработка {i + 1}: {vacancy.name}")

        # Создаем данные для процессора
        vacancy_data = {
            'hh_id': vacancy.hh_id,
            'name': vacancy.name,
            'company': vacancy.company,
            'description': vacancy.description or '',
            'skills': vacancy.skills or '',
            'url': vacancy.url
        }

        # Обрабатываем через процессор
        success = await vacancy_processor.process_vacancy(vacancy_data)

        if success:
            processed_count += 1
            logger.info("✅ Успешно обработана")
        else:
            logger.info("⏩ Не обработана (не Python или ошибка)")

    logger.info(f"\n📊 Обработано: {processed_count} из {min(2, len(unprocessed_vacancies))}")

    # Проверяем результат
    vacancies_with_letters = await db.get_vacancies_with_cover_letters()
    logger.info(f"📝 Всего с письмами в БД: {len(vacancies_with_letters)}")

    return processed_count > 0


async def main():
    logger.info("🎯 ТЕСТИРОВАНИЕ ОБРАБОТКИ ВАКАНСИЙ")
    logger.info("=" * 50)

    # Инициализация БД
    await db.create_tables()

    results = {}

    # 1. Тест DeepSeek
    results['deepseek'] = await test_deepseek_connection()

    # 2. Тест генерации писем
    if results['deepseek']:
        await test_letter_generation()

    # 3. Тест обработки реальных вакансий
    results['processing'] = await test_processing_real_vacancies()

    # Итоги
    logger.info("\n" + "=" * 50)
    logger.info("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    logger.info(f"   DeepSeek API: {'✅' if results['deepseek'] else '❌'}")
    logger.info(f"   Обработка вакансий: {'✅' if results.get('processing') else '⚠️ '}")

    if results['deepseek'] and results.get('processing'):
        logger.info("\n🎉 ОБРАБОТКА ВАКАНСИЙ РАБОТАЕТ!")
    else:
        logger.info("\n⚠️  Нужно настроить DeepSeek API")
        logger.info("💡 Получи API ключ на https://platform.deepseek.com/")
        logger.info("💡 Добавь DEEPSEEK_API_KEY=твой_ключ в .env")


if __name__ == "__main__":
    asyncio.run(main())