import asyncio
from typing import List, Dict, Any
from src.api.hh_client import HHClient
from src.core.database import db
from src.services.queue_manager import RabbitMQManager
from src.core.logger import get_logger

logger = get_logger(__name__)


class VacancySearcher:
    """Сервис для поиска, сохранения и отправки вакансий на обработку"""

    def __init__(self):
        self.hh_client = HHClient()
        self.rabbitmq = RabbitMQManager()

    async def search_and_process_vacancies(self, search_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Основной метод: поиск, сохранение и отправка вакансий

        Returns:
            Dict с статистикой выполнения
        """
        logger.info("Начинаем поиск и обработку вакансий...")

        # Инициализация соединений
        await self._initialize_services()

        try:
            # Поиск вакансий
            search_result = await self.hh_client.search_vacancies(search_params)
            if not search_result or not search_result.get('items'):
                logger.warning("Не найдено вакансий по заданным критериям")
                return {"success": False, "message": "No vacancies found"}

            # Получение полных данных вакансий
            vacancies_data = await self._get_complete_vacancies_data(search_result['items'])
            if not vacancies_data:
                logger.warning("Не удалось получить данные вакансий")
                return {"success": False, "message": "Failed to get vacancies data"}

            # Сохранение и отправка вакансий
            result = await self._process_vacancies_list(vacancies_data)

            logger.info("Поиск и обработка вакансий завершены")
            return result

        except Exception as e:
            logger.error(f"Ошибка в процессе поиска вакансий: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await self.rabbitmq.close()

    async def _initialize_services(self) -> None:
        """Инициализация всех необходимых сервисов"""
        await db.create_tables()
        if not await self.rabbitmq.connect():
            raise Exception("Не удалось подключиться к RabbitMQ")

    async def _get_complete_vacancies_data(self, vacancy_items: List[Dict]) -> List[Dict]:
        """Получение полных данных вакансий"""
        logger.info(f"Загружаем полные данные для {len(vacancy_items)} вакансий...")

        vacancies_data = await self.hh_client.get_multiple_vacancies_details(vacancy_items)
        logger.info(f"Загружено {len(vacancies_data)} вакансий с полными данными")

        return vacancies_data

    async def _process_vacancies_list(self, vacancies_data: List[Dict]) -> Dict[str, Any]:
        """Обработка списка вакансий: сохранение и отправка в очередь"""
        stats = {
            "total_found": len(vacancies_data),
            "new_saved": 0,
            "duplicates": 0,
            "sent_to_queue": 0,
            "errors": 0
        }

        for vacancy_data in vacancies_data:
            try:
                # Сохраняем вакансию в БД
                vacancy = await db.save_vacancy(vacancy_data)

                if vacancy:
                    stats["new_saved"] += 1
                    logger.info(f"Новая вакансия: {vacancy_data['name']}")

                    # Отправляем в очередь на обработку
                    if await self.rabbitmq.send_vacancy_to_queue(vacancy_data):
                        stats["sent_to_queue"] += 1
                        logger.debug(f"Отправлена в очередь: {vacancy_data['name']}")
                    else:
                        stats["errors"] += 1
                        logger.error(f"Ошибка отправки в очередь: {vacancy_data['name']}")
                else:
                    stats["duplicates"] += 1
                    logger.debug(f"Дубликат: {vacancy_data['name']}")

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Ошибка обработки вакансии {vacancy_data['name']}: {e}")

        # Логируем итоговую статистику
        self._log_processing_stats(stats)
        return {"success": True, "stats": stats}

    def _log_processing_stats(self, stats: Dict[str, Any]) -> None:
        """Логирование статистики обработки"""
        logger.info("СТАТИСТИКА ОБРАБОТКИ ВАКАНСИЙ:")
        logger.info(f"  Всего найдено: {stats['total_found']}")
        logger.info(f"   Новых сохранено: {stats['new_saved']}")
        logger.info(f"   Дубликатов: {stats['duplicates']}")
        logger.info(f"   Отправлено в очередь: {stats['sent_to_queue']}")
        logger.info(f"   Ошибок: {stats['errors']}")

    async def test_services(self) -> bool:
        """Тестирование всех сервисов"""
        logger.info("Тестирование сервисов...")

        try:
            # Тест БД
            await db.create_tables()
            logger.info("База данных: OK")

            # Тест RabbitMQ
            if await self.rabbitmq.connect():
                await self.rabbitmq.close()
                logger.info("RabbitMQ: OK")
            else:
                logger.error("RabbitMQ: FAILED")
                return False

            # Тест HH API
            if await self.hh_client.test_connection():
                logger.info("HH.ru API: OK")
            else:
                logger.error("HH.ru API: FAILED")
                return False

            logger.info("Все сервисы работают корректно!")
            return True

        except Exception as e:
            logger.error(f"Ошибка тестирования сервисов: {e}")
            return False


# Глобальный экземпляр для удобства
vacancy_searcher = VacancySearcher()


# Утилитарные функции для быстрого использования
async def search_new_vacancies(search_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Поиск новых вакансий"""
    return await vacancy_searcher.search_and_process_vacancies(search_params)


async def test_all_services() -> bool:
    """Тестирование всех сервисов"""
    return await vacancy_searcher.test_services()
