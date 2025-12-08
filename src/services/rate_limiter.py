import asyncio
import time
from typing import Optional
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Ограничитель частоты запросов для соблюдения лимитов HH.ru"""

    def __init__(self, requests_per_hour: Optional[int] = None):
        self.requests_per_hour = requests_per_hour or settings.REQUESTS_PER_HOUR
        self.delay = 3600 / self.requests_per_hour  # секунд между запросами
        self.last_request: float = 0

        logger.info(
            f"Rate limiter настроен: {self.requests_per_hour} запросов/час (~{self.delay:.0f} сек между откликами)")

    async def wait_if_needed(self) -> None:
        """Ждет если нужно соблюдать лимиты"""
        if self.last_request == 0:
            self.last_request = time.time()
            return

        now = time.time()
        time_since_last = now - self.last_request

        if time_since_last < self.delay:
            wait_time = self.delay - time_since_last

            # обратный отсчёт
            minutes = int(wait_time // 60)
            seconds = int(wait_time % 60)
            logger.info(f"Отправка через: {minutes:02d}:{seconds:02d}")

            # Обновляем каждую секунду
            while wait_time > 0:
                minutes = int(wait_time // 60)
                seconds = int(wait_time % 60)
                print(f"Отправка через: {minutes:02d}:{seconds:02d}", end='\r', flush=True)
                await asyncio.sleep(1)
                wait_time -= 1

            print(" " * 50, end='\r')  # Очищаем строку
            logger.info("Отправка сейчас!")

        self.last_request = time.time()

    def get_remaining_time(self) -> float:
        """Возвращает оставшееся время до следующего запроса"""
        if self.last_request == 0:
            return 0

        now = time.time()
        time_since_last = now - self.last_request

        if time_since_last >= self.delay:
            return 0
        else:
            return self.delay - time_since_last