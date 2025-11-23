hh_job_bot/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Все настройки
│   │   ├── database.py         # Работа с БД
│   │   ├── models.py           # Модели
│   │   └── logger.py          # Логирование
│   ├── api/
│   │   ├── __init__.py
│   │   ├── hh_api.py          # API HH.ru
│   │   ├── hh_responder.py    # Отправка откликов
│   │   └── deepseek_client.py # Генерация писем
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vacancy_processor.py # Обработка вакансий
│   │   ├── queue_manager.py     # RabbitMQ
│   │   └── rate_limiter.py     # Лимиты
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── vacancy_worker.py   # Воркер обработки
│   │   └── sender_worker.py    # Воркер отправки
│   └── cli/
│       ├── __init__.py
│       ├── commands.py         # CLI команды
│       └── utils.py            # Утилиты
├── scripts/
│   ├── deploy.sh
│   ├── setup.sh
│   └── health_check.sh
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
├── requirements.txt
├── .env.example
└── main.py                     # Точка входа