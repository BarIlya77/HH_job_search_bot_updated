from src.core.database import db
from src.api.deepseek_client import DeepSeekClient
from src.services.queue_manager import RabbitMQManager
from src.core.logger import get_logger

logger = get_logger(__name__)

class VacancyProcessor:
    def __init__(self):
        self.deepseek = DeepSeekClient()
        self.rabbitmq = RabbitMQManager()

    async def process_vacancy(self, vacancy_data):
        """Обрабатывает вакансию: генерирует письмо и отправляет в очередь"""
        logger.info(f"🔧 Обработка: {vacancy_data['name']}")

        # Генерируем сопроводительное письмо
        cover_letter = await self.deepseek.generate_cover_letter(vacancy_data)

        if cover_letter:
            logger.info("✅ Письмо сгенерировано")

            # Находим вакансию в БД
            vacancy = await db.get_vacancy_by_hh_id(vacancy_data['hh_id'])

            if vacancy:
                # Сохраняем письмо в БД
                success = await db.mark_cover_letter_generated(vacancy.id, cover_letter)

                if success:
                    logger.info(f"💾 Письмо сохранено: {vacancy_data['name']}")

                    # Отправляем в очередь для отправки
                    cover_data = {
                        'vacancy_id': vacancy_data['hh_id'],
                        'vacancy_name': vacancy_data['name'],
                        'company': vacancy_data['company'],
                        'cover_letter': cover_letter,
                        'url': vacancy_data['url']
                    }

                    if await self.rabbitmq.send_cover_letter_to_queue(cover_data):
                        logger.info("📤 Письмо в очереди отправки")
                        return True
                    else:
                        logger.error("❌ Ошибка отправки в очередь")
                        return False
                else:
                    logger.error("❌ Ошибка сохранения письма")
                    return False
            else:
                logger.error(f"❌ Вакансия не найдена в БД")
                return False
        else:
            logger.info("⏩ Пропуск: не Python-вакансия")
            return False

# Глобальный экземпляр
vacancy_processor = VacancyProcessor()
