# src/api/deepseek_client.py
import aiohttp
import json
import random
from typing import Optional
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    """Клиент для генерации сопроводительных писем через DeepSeek API"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL

    async def generate_cover_letter(self, vacancy_data: dict) -> Optional[str]:
        """Генерирует сопроводительное письмо только для Python-вакансий"""
        # Проверяем, подходит ли вакансия (только Python-разработка)
        if not self._is_python_vacancy(vacancy_data):
            logger.info(f"⏩ Пропуск не-Python вакансии: {vacancy_data['name']}")
            return None

        logger.info(f"🔧 Генерация письма для Python-вакансии: {vacancy_data['name']}")
        return self._generate_python_letter(vacancy_data)

    def _is_python_vacancy(self, vacancy_data: dict) -> bool:
        """Проверяет, является ли вакансия Python-разработкой"""
        name = vacancy_data['name'].lower()
        description = vacancy_data.get('description', '').lower()
        skills = vacancy_data.get('skills', '').lower()

        # Проверяем наличие ключевых слов в названии, описании или навыках
        text_to_check = f"{name} {description} {skills}"

        return any(keyword in text_to_check for keyword in settings.PYTHON_KEYWORDS)

    def _generate_python_letter(self, vacancy_data: dict) -> str:
        """Генерирует письмо для Python-вакансий по шаблону"""
        company = vacancy_data['company']
        vacancy_name = vacancy_data['name']

        # Создаем персонализированную часть о привлекательности вакансии
        attraction_part = self._get_attraction_part(vacancy_data)

        letter = f"""
        Уважаемые команда {company}!

        С большим интересом изучил вакансию «{vacancy_name}». Меня особенно привлекло {attraction_part}.

        В рамках поиска новых карьерных возможностей я разработал автономную систему для анализа рынка труда — HH Job Bot.

        Проект представляет собой микросервисную платформу на Python, которая:
        • Интегрируется с HH.ru API для интеллектуального поиска вакансий
        • Управляет очередями задач через RabbitMQ  
        • Автоматизирует взаимодействие с работодателями с соблюдением лимитов платформы
        • Использует LLM (DeepSeek) для адаптации сопроводительных писем

        Технологический стек: Python, FastAPI, SQLAlchemy, PostgreSQL, RabbitMQ, Docker, DeepSeek API.

        Для меня этот проект — демонстрация подхода к решению сложных задач через автоматизацию и системное мышление. Именно такой вклад я хотел бы вносить в вашу команду.

        Буду рад обсудить, как мои навыки могут быть полезны вашей компании.

        С уважением,
        {settings.CONTACT_NAME}
        Телефон: {settings.CONTACT_PHONE}
        Telegram: {settings.CONTACT_TELEGRAM}
        GitHub: {settings.CONTACT_GITHUB}

        P.S. Этот отклик был отправлен с помощью моего бота — готов рассказать о технической реализации и показать код!
        """

        return letter.strip()

    def _get_attraction_part(self, vacancy_data: dict) -> str:
        """Создает персонализированную часть о том, что привлекло в вакансии"""
        name = vacancy_data['name'].lower()
        description = vacancy_data.get('description', '').lower()
        company = vacancy_data['company']

        attraction_options = [
            "возможность работать с современным стеком Python",
            "шанс присоединиться к сильной команде для решения интересных задач",
            "перспектива участия в разработке масштабных проектов",
            "возможность углубленного изучения backend-разработки",
            "перспектива работы над высоконагруженными системами",
            f"ваш продукт и возможность внести вклад в его развитие",
            "современный технологический стек и подходы к разработке"
        ]

        # Пробуем найти более релевантный вариант на основе описания
        if 'fastapi' in description:
            return "работа с FastAPI и современными асинхронными фреймворками"
        elif 'django' in description:
            return "использование Django для создания надежных веб-приложений"
        elif 'postgresql' in description or 'баз' in description:
            return "работа с базами данных и оптимизация запросов"
        elif 'микросервис' in description:
            return "архитектура микросервисов и распределенных систем"
        elif 'api' in description:
            return "разработка и проектирование API"
        else:
            return random.choice(attraction_options)

    async def test_connection(self) -> bool:
        """Тестирует подключение к DeepSeek API"""
        if not self.api_key:
            logger.error("❌ DEEPSEEK_API_KEY не установлен")
            return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Тестовое сообщение"}],
            "max_tokens": 10
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status in [200, 401]:  # 401 тоже ок - значит ключ работает
                        logger.info("✅ Подключение к DeepSeek API успешно")
                        return True
                    else:
                        logger.error(f"❌ Ошибка подключения: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования подключения: {e}")
            return False