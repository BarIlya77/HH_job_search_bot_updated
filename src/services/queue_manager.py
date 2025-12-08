import aio_pika
import json
import asyncio
from typing import Dict, Any, Optional
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class RabbitMQManager:
    """Менеджер для работы с очередями RabbitMQ"""

    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.is_connected = False

    async def connect(self, max_retries: int = 5) -> bool:
        """Подключение к RabbitMQ с повторными попытками"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Попытка подключения к RabbitMQ ({attempt + 1}/{max_retries})...")
                self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self.channel = await self.connection.channel()

                # Устанавливаем лимит неподтвержденных сообщений
                await self.channel.set_qos(prefetch_count=1)

                # Объявляем очереди
                await self.channel.declare_queue(settings.QUEUE_VACANCIES, durable=True)
                await self.channel.declare_queue(settings.QUEUE_COVER_LETTERS, durable=True)

                self.is_connected = True
                logger.info("Подключение к RabbitMQ установлено")
                return True

            except Exception as e:
                logger.error(f"Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                if attempt < max_retries - 1:
                    logger.info("Повторная попытка через 5 секунд...")
                    await asyncio.sleep(5)

        logger.error("Не удалось подключиться к RabbitMQ после всех попыток")
        return False

    async def ensure_connection(self) -> bool:
        """Проверяет и восстанавливает соединение при необходимости"""
        if not self.is_connected or (self.connection and self.connection.is_closed):
            logger.warning("Восстановление соединения с RabbitMQ...")
            return await self.connect()
        return True

    async def send_vacancy_to_queue(self, vacancy_data: Dict[str, Any]) -> bool:
        """Отправляет вакансию в очередь на обработку"""
        if not await self.ensure_connection():
            return False

        try:
            message_body = json.dumps(vacancy_data, ensure_ascii=False)
            message = aio_pika.Message(
                body=message_body.encode('utf-8'),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            await self.channel.default_exchange.publish(
                message,
                routing_key=settings.QUEUE_VACANCIES
            )
            logger.info(f"Вакансия отправлена в очередь: {vacancy_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Ошибка отправки в очередь: {e}")
            self.is_connected = False
            return False

    async def send_cover_letter_to_queue(self, cover_letter_data: Dict[str, Any]) -> bool:
        """Отправляет сопроводительное письмо в очередь на отправку"""
        if not await self.ensure_connection():
            return False

        try:
            message_body = json.dumps(cover_letter_data, ensure_ascii=False)
            message = aio_pika.Message(
                body=message_body.encode('utf-8'),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            await self.channel.default_exchange.publish(
                message,
                routing_key=settings.QUEUE_COVER_LETTERS
            )
            logger.info("Сопроводительное письмо отправлено в очередь отправки")
            return True

        except Exception as e:
            logger.error(f"Ошибка отправки письма в очередь: {e}")
            self.is_connected = False
            return False

    async def close(self) -> None:
        """Закрывает соединение"""
        if self.connection:
            await self.connection.close()
            self.is_connected = False
            logger.info("Соединение с RabbitMQ закрыто")

    async def get_queue_stats(self) -> Dict[str, int]:
        """Получает статистику по очередям"""
        if not await self.ensure_connection():
            return {}

        try:
            stats = {}

            # Получаем очередь вакансий
            queue_vacancies = await self.channel.declare_queue(settings.QUEUE_VACANCIES, passive=True)
            stats[settings.QUEUE_VACANCIES] = queue_vacancies.declaration_result.message_count

            # Получаем очередь писем
            queue_letters = await self.channel.declare_queue(settings.QUEUE_COVER_LETTERS, passive=True)
            stats[settings.QUEUE_COVER_LETTERS] = queue_letters.declaration_result.message_count

            return stats

        except Exception as e:
            logger.error(f"Ошибка получения статистики очередей: {e}")
            return {}
