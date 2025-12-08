# test_services.py
# !/usr/bin/env python3
"""
Тестовый скрипт для проверки всех сервисов HH Job Bot
"""

import asyncio
import sys
import os

# Добавляем src в путь для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.logger import get_logger
from src.services.vacancy_searcher import test_all_services, search_new_vacancies
from src.core.database import db
from src.services.queue_manager import RabbitMQManager

logger = get_logger(__name__)


async def test_database():
    """Тестирование базы данных"""
    logger.info("Тестирование базы данных...")
    try:
        await db.create_tables()

        # Проверяем существующие вакансии
        vacancies = await db.get_all_vacancies()
        logger.info(f"В базе данных: {len(vacancies)} вакансий")

        # Статистика
        stats = {
            'total': len(vacancies),
            'unprocessed': len(await db.get_unprocessed_vacancies()),
            'with_letters': len(await db.get_vacancies_with_cover_letters()),
        }

        logger.info(f"  Всего: {stats['total']}")
        logger.info(f"  Необработанных: {stats['unprocessed']}")
        logger.info(f"  С письмами: {stats['with_letters']}")

        return True
    except Exception as e:
        logger.error(f"Ошибка тестирования БД: {e}")
        return False


async def test_rabbitmq():
    """Тестирование RabbitMQ"""
    logger.info("Тестирование RabbitMQ...")
    rabbitmq = RabbitMQManager()
    try:
        if await rabbitmq.connect():
            # Проверяем статистику очередей
            stats = await rabbitmq.get_queue_stats()
            logger.info(f"Статистика очередей: {stats}")
            await rabbitmq.close()
            return True
        else:
            logger.error("Не удалось подключиться к RabbitMQ")
            return False
    except Exception as e:
        logger.error(f"Ошибка тестирования RabbitMQ: {e}")
        return False


async def test_vacancy_search():
    """Тестовый поиск вакансий (ограниченный)"""
    logger.info("Тестовый поиск вакансий...")

    # Используем ограниченные параметры для теста
    test_params = {
        "per_page": 2,  # Всего 2 вакансии для теста
        "page": 0
    }

    try:
        result = await search_new_vacancies(test_params)

        if result.get('info'):
            stats = result.get('stats', {})
            logger.info("Поиск вакансий выполнен успешно!")
            logger.info(f"Результаты: {stats}")
            return True
        else:
            logger.error(f"Ошибка поиска: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"Ошибка при тестовом поиске: {e}")
        return False


async def send_test_vacancy_to_queue():
    """Отправка тестовой вакансии в очередь для проверки воркера"""
    logger.info("Отправка тестовой вакансии в очередь...")

    rabbitmq = RabbitMQManager()
    try:
        if await rabbitmq.connect():
            test_vacancy = {
                'hh_id': 'test_vacancy_001',
                'name': 'Python Developer (Test)',
                'company': 'Test Company Inc.',
                'salary_from': 100000,
                'salary_to': 150000,
                'salary_currency': 'RUR',
                'experience': 'Нет опыта',
                'employment': 'Полная занятость',
                'description': 'Ищем Python разработчика с опытом работы с FastAPI и PostgreSQL. Требования: Python, FastAPI, SQL, Docker.',
                'skills': 'Python, FastAPI, PostgreSQL, Docker',
                'url': 'https://hh.ru/vacancy/test_001'
            }

            if await rabbitmq.send_vacancy_to_queue(test_vacancy):
                logger.info("Тестовая вакансия отправлена в очередь!")

                # Проверяем статистику после отправки
                stats = await rabbitmq.get_queue_stats()
                logger.info(f"Очередь вакансий: {stats.get('vacancies_to_process', 0)} сообщений")

                await rabbitmq.close()
                return True
            else:
                logger.error("Не удалось отправить тестовую вакансию")
                await rabbitmq.close()
                return False
        else:
            logger.error("Не удалось подключиться к RabbitMQ")
            return False

    except Exception as e:
        logger.error(f"Ошибка отправки тестовой вакансии: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    logger.info("ЗАПУСК ТЕСТИРОВАНИЯ СЕРВИСОВ HH JOB BOT")
    logger.info("=" * 50)

    results = {}

    # 1. Тест всех сервисов (быстрая проверка)
    logger.info("\n1.  БЫСТРАЯ ПРОВЕРКА ВСЕХ СЕРВИСОВ")
    results['all_services'] = await test_all_services()

    # 2. Детальное тестирование компонентов
    logger.info("\n2.  ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ КОМПОНЕНТОВ")

    logger.info("\n2.1  ТЕСТ БАЗЫ ДАННЫХ")
    results['database'] = await test_database()

    logger.info("\n2.2  ТЕСТ RABBITMQ")
    results['rabbitmq'] = await test_rabbitmq()

    logger.info("\n2.3  ТЕСТ ПОИСКА ВАКАНСИЙ")
    results['vacancy_search'] = await test_vacancy_search()

    logger.info("\n2.4 ТЕСТ ОЧЕРЕДИ")
    results['queue_test'] = await send_test_vacancy_to_queue()

    # Итоговый отчет
    logger.info("\n" + "=" * 50)
    logger.info("ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    logger.info("=" * 50)

    for test_name, info in results.items():
        status = "PASS" if info else "FAIL"
        logger.info(f"{status} {test_name}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    logger.info(f"\n РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")

    if passed_tests == total_tests:
        logger.info("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        logger.error("НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
        return False


if __name__ == "__main__":
    info = asyncio.run(main())
    sys.exit(0 if info else 1)
