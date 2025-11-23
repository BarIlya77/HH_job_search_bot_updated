import aiohttp
from typing import Optional
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class HHResponder:
    """Клиент для отправки откликов на HH.ru"""

    def __init__(self):
        self.access_token = settings.HH_ACCESS_TOKEN
        self.resume_id = settings.HH_RESUME_ID
        self.base_url = "https://api.hh.ru"

    async def send_application(self, vacancy_id: str, cover_letter: str) -> bool:
        """Отправляет отклик на вакансию через официальное API HH.ru"""
        if not self.access_token:
            logger.error("HH_ACCESS_TOKEN не установлен в .env")
            return False

        if not self.resume_id:
            logger.error("HH_RESUME_ID не установлен в .env")
            return False

        url = f"{self.base_url}/negotiations"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION} ({settings.CONTACT_EMAIL})",
        }

        data = {
            "vacancy_id": str(vacancy_id).strip(),
            "resume_id": str(self.resume_id).strip(),
            "message": cover_letter
        }

        # Логируем детали запроса
        logger.info(f"📨 Отправка отклика на вакансию {vacancy_id}")
        logger.debug(f"Заголовки: { {k: '***' if k == 'Authorization' else v for k, v in headers.items()} }")
        logger.debug(f"Данные: {data}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:

                    response_text = await response.text()
                    logger.debug(f"Статус ответа: {response.status}, Тело: {response_text}")

                    if response.status == 201:
                        logger.info(f"✅ Отклик успешно отправлен на вакансию {vacancy_id}")
                        return True
                    elif response.status == 403:
                        logger.error(f"❌ Ошибка доступа (403): {response_text}")
                        return False
                    elif response.status == 429:
                        logger.warning("⚠️ Превышен лимит запросов к API HH.ru")
                        return False
                    else:
                        logger.error(f"❌ Ошибка {response.status}: {response_text}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка сети: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            return False

    async def check_application_status(self, vacancy_id: str) -> Optional[str]:
        """Проверяет, был ли уже отправлен отклик на вакансию"""
        if not self.access_token:
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.base_url}/negotiations?vacancy_id={vacancy_id}",
                        headers=headers
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        if data['items']:
                            state = data['items'][0]['state']['id']
                            logger.info(f"ℹ️ Статус отклика на {vacancy_id}: {state}")
                            return state
                    return None

        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса: {e}")
            return None

    async def test_connection(self) -> bool:
        """Тестирует подключение к API HH.ru"""
        if not self.access_token:
            logger.error("❌ HH_ACCESS_TOKEN не установлен")
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/me", headers=headers) as response:
                    if response.status == 200:
                        logger.info("✅ Подключение к HH.ru API успешно")
                        return True
                    else:
                        logger.error(f"❌ Ошибка подключения: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования подключения: {e}")
            return False
