# HH Job Search Bot 🤖

Автоматизированная система для поиска вакансий, генерации писем и отправки откликов на HH.ru.

## 🚀 Быстрый старт

## 1. Настройка
```bash
# Клонирование
git clone https://github.com/BarIlya77/HH_job_search_bot_updated
cd HH_job_search_bot_updated

# Настройка окружения
cp .env.example .env
# Заполните .env реальными API ключами
```

## 2. Запуск без Docker
```bash
# Установка зависимостей
pip install -r requirements.txt

# В разных терминалах:
python -m src.workers.search_worker      # Поиск
python -m src.workers.vacancy_worker     # Обработка
python -m src.workers.sender_worker      # Отправка
```
## 3. Запуск в Docker

### Настройка симлинка (если Docker файлы в папке docker)

```bash
# Создание симлинка для удобного запуска
ln -s docker/docker-compose.yml docker-compose.yml

# Проверка
ls -la docker-compose.yml
# Должно показать: docker-compose.yml -> docker/docker-compose.yml


docker-compose up -d

# Проверка статуса
docker-compose exec search-worker python main.py status
```



## 📊 Мониторинг

### Статистика
```bash
# Локально
python main.py status

# В Docker
docker-compose exec search-worker python main.py status
```
### Логи
```bash
docker-compose logs -f search-worker    # поиск
docker-compose logs -f process-worker   # обработка
docker-compose logs -f send-worker      # отправка
```


### ⚙️ Конфигурация

```bash
Основные настройки в .env:

env
HH_ACCESS_TOKEN=ваш_токен
HH_RESUME_ID=id_резюме
DEEPSEEK_API_KEY=ключ_deepseek
BOT_MODE=automatic  # или interactive
SEARCH_INTERVAL=3600  # секунд
REQUESTS_PER_HOUR=5   # лимит HH.ru
```


### 🔧 Управление

### Остановка
```bash
docker-compose down
# С очисткой данных
docker-compose down -v
```
### 🏗️ Архитектура
```text
search-worker → RabbitMQ → process-worker → RabbitMQ → send-worker
    ↓              ↓             ↓              ↓         ↓
  Поиск       Очередь      Обработка     Очередь    Отправка
              вакансий                  писем      откликов
```
### Структура проекта
```text
hh_job_bot_updated/
├── src/
│   ├── core/						# ⚙️ Ядро
│   │   ├── __init__.py
│   │   ├── config.py            	# Все настройки
│   │   ├── database.py          	# Работа с БД
│   │   ├── models.py            	# Модели
│   │   └── logger.py            	# Логирование
│   ├── api/					 	# 🌐 API клиенты
│   │   ├── __init__.py
│   │   ├── hh_api.py            	# API HH.ru
│   │   ├── hh_responder.py      	# Отправка откликов
│   │   └── deepseek_client.py   	# Генерация писем
│   ├── services/					# ⚡ Бизнес-логика
│   │   ├── __init__.py
│   │   ├── vacancy_processor.py 	# Обработка вакансий
│   │   ├── queue_manager.py      	# RabbitMQ
│   │   └── rate_limiter.py       	# Лимиты
│   ├── workers/				  	# 👷 Воркеры
│   │   ├── __init__.py
│   │   ├── vacancy_worker.py    	# Воркер обработки
│   │   ├── search_worker.py     	# Воркер поиска
│   │   └── sender_worker.py     	# Воркер отправки
│   └── cli/
│       ├── __init__.py
│       └── commands.py          	# CLI команды
├── scripts/						# 📜 Скрипты
│   ├── clean_database.py
│   └── clear_queues.py
├── docker/							# 🐳 Docker
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
├── requirements.txt
├── .env.example
└── main.py                      # Точка входа
```

## 🤝 Режимы работы
### Автоматический (BOT_MODE=automatic)
- Автоматический поиск каждые N секунд
- Автоматическая генерация писем
- Автоматическая отправка с соблюдением лимитов

### Интерактивный (BOT_MODE=interactive)
- Подтверждение перед отправкой каждого отклика
- Ручной контроль лимитов
- Просмотр писем перед отправкой



## 📝 Примечания
- Соблюдайте лимиты HH.ru (5 откликов/час)
- Тестируйте в интерактивном режиме перед автоматизацией
- Используйте ответственно


# Счастливого поиска работы! 🎯