"""
Диагностика сообщений в RabbitMQ
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import get_logger
from src.services.queue_manager import RabbitMQManager
from src.core.config import settings

logger = get_logger(__name__)

async def inspect_messages():
    """Просматривает сообщения в очередях - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    rabbitmq = RabbitMQManager()

    if not await rabbitmq.connect():
        logger.error("❌ Не удалось подключиться к RabbitMQ")
        return

    try:
        # ✅ ПРАВИЛЬНЫЙ ВЫЗОВ
        queue = await rabbitmq.channel.declare_queue(settings.QUEUE_COVER_LETTERS, passive=True)
        message_count = queue.declaration_result.message_count
        logger.info(f"📊 Сообщений в очереди писем: {message_count}")

        if message_count > 0:
            # Получаем первое сообщение
            message = await queue.get(no_ack=False)  # no_ack=False чтобы не удалять сообщение
            if message:
                logger.info("🔍 Диагностика сообщения:")
                logger.info(f"📦 Размер: {len(message.body)} байт")

                # Пробуем разные кодировки
                encodings = ['utf-8', 'latin-1', 'cp1251', 'ascii']
                for encoding in encodings:
                    try:
                        decoded = message.body.decode(encoding)
                        logger.info(f"✅ Успешно декодировано как {encoding}: {decoded[:100]}...")

                        # Пробуем распарсить как JSON
                        import json
                        data = json.loads(decoded)
                        logger.info(f"📋 JSON данные: {list(data.keys())}")
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError) as e:
                        logger.info(f"❌ Не удалось декодировать как {encoding}: {e}")

                # Подтверждаем сообщение чтобы оно осталось в очереди
                await message.ack()

    except Exception as e:
        logger.error(f"❌ Ошибка диагностики: {e}")
    finally:
        await rabbitmq.close()


if __name__ == "__main__":
    asyncio.run(inspect_messages())