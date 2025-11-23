# src/api/hh_client.py
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class HHClient:
    """Клиент для работы с API HH.ru"""

    def __init__(self):
        self.base_url = settings.HH_API_URL
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.request_delay = settings.REQUEST_DELAY

    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Асинхронный метод для выполнения запросов с обработкой ошибок"""
        async with self.semaphore:
            await asyncio.sleep(self.request_delay)

            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, params=params) as response:
                        logger.info("=" * 50)
                        logger.info(f"🔧 Параметры поиска: {params}")
                        logger.info("=" * 50)
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"HTTP {response.status} для {url}")
                            return None
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка при запросе к {url}: {e}")
                return None
            except asyncio.TimeoutError:
                logger.error(f"Таймаут при запросе к {url}")
                return None

    async def search_vacancies(self, custom_params: Optional[Dict] = None) -> Optional[Dict]:
        """Поиск вакансий по заданным параметрам"""
        params = {
            "text": settings.SEARCH_QUERY,
            "area": settings.SEARCH_AREAS,
            "per_page": settings.SEARCH_PER_PAGE,
            "page": 0,
            "order_by": "publication_time",
        }

        if custom_params:
            params.update(custom_params)

        logger.info("🔍 Поиск вакансий с параметрами:")
        for key, value in params.items():
            logger.info(f"  {key}: {value}")

        result = await self._make_request(self.base_url, params)

        if result:
            await self._log_search_stats(result)
            return result
        else:
            logger.error("Не удалось получить данные от HH API")
            return None

    async def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получение полных деталей вакансии"""
        url = f"{self.base_url}/{vacancy_id}"
        return await self._make_request(url)

    async def get_complete_vacancy_data(self, vacancy_list_item: Dict) -> Optional[Dict]:
        """Получает полные данные вакансии по ID из списка"""
        vacancy_id = vacancy_list_item['id']
        full_details = await self.get_vacancy_details(vacancy_id)

        if full_details:
            return self._parse_vacancy_data(full_details)
        else:
            logger.warning(f"Не удалось загрузить детали для {vacancy_id}, используем сниппет")
            return self._parse_vacancy_data(vacancy_list_item)

    async def get_multiple_vacancies_details(self, vacancy_items: List[Dict]) -> List[Dict]:
        """Параллельная загрузка полных данных для списка вакансий"""
        tasks = []
        for item in vacancy_items:
            task = self.get_complete_vacancy_data(item)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        complete_vacancies = []
        for result in results:
            if not isinstance(result, Exception) and result is not None:
                complete_vacancies.append(result)

        return complete_vacancies

    async def _log_search_stats(self, result: Dict) -> None:
        """Логирование статистики поиска"""
        if 'found' in result:
            logger.info(f"=== РЕЗУЛЬТАТЫ ПОИСКА ===")
            logger.info(f"Найдено вакансий: {result['found']}")
            logger.info(f"Страница: {result.get('page', 0) + 1} из {result.get('pages', 1)}")
            logger.info(f"Получено ID: {len(result.get('items', []))}")

    def _parse_vacancy_data(self, raw_vacancy: Dict) -> Dict[str, Any]:
        """Парсинг данных вакансии в унифицированный формат"""
        # Зарплата
        salary_from = salary_to = salary_currency = None
        if raw_vacancy.get('salary'):
            salary = raw_vacancy['salary']
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            salary_currency = salary.get('currency')

        # Описание
        description = raw_vacancy.get('description', '')
        if not description and raw_vacancy.get('snippet'):
            snippet = raw_vacancy['snippet']
            requirement = snippet.get('requirement', '')
            responsibility = snippet.get('responsibility', '')
            description = f"Требования: {requirement}\nОбязанности: {responsibility}"

        # Навыки
        skills = ''
        if raw_vacancy.get('key_skills'):
            skills = ', '.join([skill['name'] for skill in raw_vacancy['key_skills']])

        return {
            'hh_id': str(raw_vacancy['id']),
            'name': raw_vacancy.get('name', ''),
            'company': raw_vacancy.get('employer', {}).get('name', ''),
            'salary_from': salary_from,
            'salary_to': salary_to,
            'salary_currency': salary_currency,
            'experience': raw_vacancy.get('experience', {}).get('name', ''),
            'employment': raw_vacancy.get('employment', {}).get('name', ''),
            'description': description,
            'skills': skills,
            'url': f"https://hh.ru/vacancy/{raw_vacancy['id']}"
        }

    async def test_connection(self) -> bool:
        """Тестирование подключения к API HH.ru"""
        try:
            result = await self._make_request(f"{self.base_url}/vacancies", {"per_page": 1})
            if result:
                logger.success("✅ Подключение к HH.ru API успешно")
                return True
            else:
                logger.error("❌ Ошибка подключения к HH.ru API")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования подключения: {e}")
            return False
