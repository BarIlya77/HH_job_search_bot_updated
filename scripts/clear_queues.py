"""
Очистка очередей RabbitMQ
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import get_logger
from src.services.queue_manager import RabbitMQManager
from src.core.config import settings

logger = get_logger(__name__)

async def clear_queues():
    """Очищает все очереди"""
    rabbitmq = RabbitMQManager()
    
    if await rabbitmq.connect():
        try:
            # ✅ получаем очередь и вызываем purge()
            queue_letters = await rabbitmq.channel.declare_queue(settings.QUEUE_COVER_LETTERS, passive=True)
            await queue_letters.purge()
            logger.info("✅ Очередь писем очищена")
            
            queue_vacancies = await rabbitmq.channel.declare_queue(settings.QUEUE_VACANCIES, passive=True) 
            await queue_vacancies.purge()
            logger.info("✅ Очередь вакансий очищена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")
        finally:
            await rabbitmq.close()

if __name__ == "__main__":
    asyncio.run(clear_queues())
