import asyncio
import aio_pika
import json
from src.core.database import db
from src.services.vacancy_processor import vacancy_processor
from src.services.queue_manager import RabbitMQManager
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


async def process_vacancy_message(message: aio_pika.IncomingMessage):
    """Обрабатывает сообщение с вакансией из очереди"""
    async with message.process():
        try:
            # Декодируем сообщение
            body = message.body.decode('utf-8')
            vacancy_data = json.loads(body)

            logger.info(f"НОВАЯ ВАКАНСИЯ: {vacancy_data.get('name', 'Unknown')}")

            # Обрабатываем вакансию через процессор
            success = await vacancy_processor.process_vacancy(vacancy_data)

            if success:
                logger.info(f"Успешно обработана: {vacancy_data['name']}")
            else:
                logger.warning(f"Не обработана: {vacancy_data['name']}")

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки вакансии: {e}")


async def main():
    """Основная функция воркера"""
    logger.info("Запуск воркера обработки вакансий...")

    # Инициализация БД
    await db.create_tables()
    logger.info("База данных готова")

    # Инициализация RabbitMQ
    rabbitmq = RabbitMQManager()

    connection = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # Подключаемся к RabbitMQ
            logger.info(f"Попытка подключения к RabbitMQ ({attempt + 1}/{max_retries})...")

            if await rabbitmq.connect():
                connection = rabbitmq.connection
                break
            else:
                if attempt < max_retries - 1:
                    logger.info("Повторная попытка через 10 секунд...")
                    await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(10)

    if not connection:
        logger.error("Не удалось подключиться к RabbitMQ после всех попыток")
        return

    try:
        # Получаем очередь
        channel = rabbitmq.channel
        queue = await channel.declare_queue(settings.QUEUE_VACANCIES, durable=True)

        logger.info("Подключение к RabbitMQ установлено")
        logger.info(f"Ожидание вакансий в очереди '{settings.QUEUE_VACANCIES}'...")

        # Начинаем слушать очередь
        await queue.consume(process_vacancy_message)

        logger.info("\nВОРКЕР ЗАПУЩЕН!")
        logger.info("Ожидание сообщений... (Ctrl+C для выхода)")

        # Бесконечное ожидание
        await asyncio.Future()

    except KeyboardInterrupt:
        logger.info("\nЗавершение работы воркера...")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    finally:
        if rabbitmq:
            await rabbitmq.close()
        logger.info("Соединения закрыты")


if __name__ == "__main__":
    asyncio.run(main())
