# debug_config.py
#!/usr/bin/env python3
"""
Диагностика параметров в config.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import get_logger
from src.core.config import settings

logger = get_logger(__name__)


logger.info("ДИАГНОСТИКА CONFIG.PY")
logger.info("=" * 50)

logger.info("Текущие параметры поиска:")
logger.info(f"SEARCH_QUERY: '{settings.SEARCH_QUERY}'")
logger.info(f"SEARCH_AREAS: {settings.SEARCH_AREAS}")
logger.info(f"SEARCH_PER_PAGE: {settings.SEARCH_PER_PAGE}")
logger.info(f"Тип SEARCH_QUERY: {type(settings.SEARCH_QUERY)}")
logger.info(f"Тип SEARCH_AREAS: {type(settings.SEARCH_AREAS)}")

logger.info("\n Сравнение с рабочими параметрами:")
working_params = {
    "text": "Python",
    "area": 1,
    "per_page": 5
}

logger.info(f"Рабочий text: '{working_params['text']}'")
logger.info(f"Config SEARCH_QUERY: '{settings.SEARCH_QUERY}'")
logger.info(f"Рабочий area: {working_params['area']}")
logger.info(f"Config SEARCH_AREAS: {settings.SEARCH_AREAS}")
logger.info(f"Рабочий per_page: {working_params['per_page']}")
logger.info(f"Config SEARCH_PER_PAGE: {settings.SEARCH_PER_PAGE}")

logger.info("\nВозможные проблемы:")
logger.info("1. SEARCH_QUERY слишком сложный")
logger.info("2. SEARCH_AREAS содержит неверные коды регионов")
logger.info("3. Параметры в неправильном формате")