"""
Тест полного цикла: поиск → обработка → отправка с подтверждением
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.logger import get_logger
from src.services.vacancy_searcher import search_new_vacancies
from src.core.database import db
from src.services.queue_manager import RabbitMQManager
from src.api.hh_responder import HHResponder

logger = get_logger(__name__)


async def send_test_application():
    """Отправляет тестовый отклик с подтверждением"""
    logger.info("\n4. 📨 ТЕСТ ОТПРАВКИ ОТКЛИКА (С ПОДТВЕРЖДЕНИЕМ)")
    logger.info("=" * 50)

    responder = HHResponder()

    # Проверяем настройки
    if not responder.access_token:
        logger.error("❌ HH_ACCESS_TOKEN не установлен")
        logger.info("💡 Запусти: python src/api/hh_auth.py для настройки авторизации")
        return False

    if not responder.resume_id:
        logger.error("❌ HH_RESUME_ID не установлен")
        logger.info("💡 Запусти: python src/api/hh_auth.py для настройки авторизации")
        return False

    logger.info("✅ Настройки HH.ru найдены")
    logger.info(f"📄 Resume ID: {responder.resume_id}")

    # Создаем тестовое письмо
    test_cover_letter = """
Уважаемые команда Test Company!

С большим интересом изучил вакансию «Python Developer (Test)». Меня особенно привлекло возможность работать с современным стеком Python.

Мой опыт сосредоточен в области backend-разработки на Python. На практике я применял следующие технологии:

Backend: Python, FastAPI/Django/Flask, REST API
Базы данных: PostgreSQL, SQLite  
Инструменты: Git, Docker, Linux

Свой интерес к разработке я подкрепил созданием нескольких проектов. Ключевой из них — аналог Twitter с полной бэкенд-реализацией на FastAPI.

Ищу команду, где смогу применять и развивать свои навыки, решая реальные задачи.

Буду рад обсудить, как мои навыки могут быть полезны вашей компании.

С уважением,
Илья Баранов
Телефон: +7 902 801 68 14
Telegram: @barilya
GitHub: https://github.com/BarIlya77
"""

    # Используем тестовый ID вакансии (можно заменить на реальный)
    test_vacancy_id = "127050528"  # Замени на реальный ID для теста

    logger.info(f"🔗 Тестовая вакансия ID: {test_vacancy_id}")
    logger.info("✉️  Длина письма: {} символов".format(len(test_cover_letter)))

    # Спрашиваем подтверждение
    logger.info("\n⚠️  ВНИМАНИЕ: Это отправит РЕАЛЬНЫЙ отклик на HH.ru!")
    response = input("❓ Продолжить отправку тестового отклика? (y/N): ")

    if response.lower() != 'y':
        logger.info("🚫 Отправка отменена пользователем")
        return False

    logger.info("🔄 Отправка тестового отклика...")

    try:
        success = await responder.send_application(test_vacancy_id, test_cover_letter)

        if success:
            logger.success("✅ ТЕСТОВЫЙ ОТКЛИК УСПЕШНО ОТПРАВЛЕН!")

            # Проверяем статус отклика
            logger.info("🔍 Проверка статуса отклика...")
            status = await responder.check_application_status(test_vacancy_id)

            if status:
                logger.info(f"📊 Статус отклика: {status}")
            else:
                logger.info("ℹ️  Статус отклика: не найден (возможно еще обрабатывается)")

            return True
        else:
            logger.error("❌ Не удалось отправить тестовый отклик")
            return False

    except Exception as e:
        logger.error(f"💥 Ошибка при отправке тестового отклика: {e}")
        return False


async def test_full_cycle():
    """Тестируем полный цикл работы"""
    logger.info("🎯 ТЕСТ ПОЛНОГО ЦИКЛА РАБОТЫ")
    logger.info("=" * 50)

    # 1. Поиск и сохранение вакансий
    logger.info("\n1. 🔍 ПОИСК ВАКАНСИЙ")
    search_result = await search_new_vacancies({"per_page": 2})  # Всего 2 для теста

    if not search_result.get('success'):
        logger.error("❌ Поиск вакансий не удался")
        return False

    stats = search_result.get('stats', {})
    logger.info(f"✅ Найдено: {stats.get('new_saved', 0)} новых вакансий")

    # 2. Проверяем БД
    logger.info("\n2. 🗃️ ПРОВЕРКА БАЗЫ ДАННЫХ")
    all_vacancies = await db.get_all_vacancies()
    unprocessed = await db.get_unprocessed_vacancies()

    logger.info(f"📊 Всего вакансий: {len(all_vacancies)}")
    logger.info(f"📊 Необработанных: {len(unprocessed)}")

    # Показываем последние вакансии
    if all_vacancies:
        logger.info("\n📋 Последние вакансии в БД:")
        for i, vacancy in enumerate(all_vacancies[-3:]):  # Последние 3
            status = "🟢" if not vacancy.processed else "🟡" if not vacancy.applied else "🔵"
            logger.info(f"   {status} {vacancy.name} - {vacancy.company}")

    # 3. Проверяем очереди
    logger.info("\n3. 📨 ПРОВЕРКА ОЧЕРЕДЕЙ")
    rabbitmq = RabbitMQManager()
    if await rabbitmq.connect():
        queue_stats = await rabbitmq.get_queue_stats()
        logger.info(f"📊 Очередь вакансий: {queue_stats.get('vacancies_to_process', 0)}")
        logger.info(f"📊 Очередь писем: {queue_stats.get('cover_letters_to_send', 0)}")
        await rabbitmq.close()

    # 4. Тест отправки отклика (с подтверждением)
    send_success = await send_test_application()

    logger.info("\n" + "=" * 50)
    logger.info("🎯 ИТОГИ ТЕСТИРОВАНИЯ:")
    logger.info(f"   🔍 Поиск вакансий: {'✅' if search_result.get('success') else '❌'}")
    logger.info(f"   🗃️  База данных: {'✅' if all_vacancies else '⚠️ '}")
    logger.info(f"   📨 Очереди: {'✅' if 'vacancies_to_process' in locals() else '⚠️ '}")
    logger.info(f"   ✉️  Отправка откликов: {'✅' if send_success else '❌'}")

    if send_success:
        logger.info("\n💡 СИСТЕМА ГОТОВА К РАБОТЕ!")
        logger.info("🚀 Дальнейшие шаги:")
        logger.info("   1. Запусти воркер обработки: python main.py worker vacancy")
        logger.info("   2. Запусти воркер отправки: python main.py worker sender")
        logger.info("   3. Для поиска новых вакансий: python main.py search")
    else:
        logger.info("\n⚠️  Нужно настроить отправку откликов:")
        logger.info("   - Запусти: python src/api/hh_auth.py")
        logger.info("   - Получи ACCESS_TOKEN и RESUME_ID")
        logger.info("   - Добавь их в .env файл")

    return search_result.get('success') and send_success


async def main():
    success = await test_full_cycle()

    if success:
        logger.info("\n✅ ПОЛНЫЙ ЦИКЛ ПРОЙДЕН УСПЕШНО!")
    else:
        logger.error("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)