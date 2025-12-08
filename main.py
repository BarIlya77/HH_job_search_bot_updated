"""
HH Job Bot - Автоматизация поиска работы на HH.ru
"""

import asyncio
import typer
from typing import Optional
import sys
import os

from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

app = typer.Typer(
    name="hh-bot",
    help="Автоматизация поиска работы на HH.ru",
    rich_markup_mode="rich"
)


@app.command()
def version():
    """Показать версию приложения"""
    typer.echo(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    typer.echo(f"👤 {settings.CONTACT_NAME}")


@app.command()
def config():
    """Показать текущую конфигурацию"""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    table = Table(title="Конфигурация HH Job Bot")
    table.add_column("Настройка", style="cyan")
    table.add_column("Значение", style="green")
    
    table.add_row("APP_NAME", settings.APP_NAME)
    table.add_row("APP_VERSION", settings.APP_VERSION)
    table.add_row("DATABASE_URL", settings.DATABASE_URL)
    table.add_row("RABBITMQ_URL", settings.RABBITMQ_URL)
    table.add_row("SEARCH_QUERY", settings.SEARCH_QUERY)
    table.add_row("SEARCH_AREAS", str(settings.SEARCH_AREAS))
    table.add_row("HH_ACCESS_TOKEN", "Установлен" if settings.HH_ACCESS_TOKEN else "Отсутствует")
    table.add_row("HH_RESUME_ID", settings.HH_RESUME_ID or "Отсутствует")
    table.add_row("DEEPSEEK_API_KEY", "Установлен" if settings.DEEPSEEK_API_KEY else "Отсутствует")
    
    console.print(table)


@app.command()
def worker(
    worker_type: str = typer.Argument(..., help="Тип воркера: vacancy или sender")
):
    """Запуск воркера обработки"""
    if worker_type == "vacancy":
        from src.workers.vacancy_worker import main as vacancy_main
        asyncio.run(vacancy_main())
    elif worker_type == "sender":
        from src.workers.sender_worker import main as sender_main
        asyncio.run(sender_main())
    else:
        typer.echo(f"Неизвестный тип воркера: {worker_type}")
        typer.echo("Доступные типы: vacancy, sender")


@app.command()
def search():
    """Поиск новых вакансий"""
    from src.services.vacancy_searcher import search_new_vacancies
    
    typer.echo("Поиск новых вакансий...")
    result = asyncio.run(search_new_vacancies())
    
    if result.get('success'):
        stats = result.get('stats', {})
        typer.echo(f"Найдено: {stats.get('new_saved', 0)} новых вакансий")
        typer.echo(f"Отправлено в очередь: {stats.get('sent_to_queue', 0)}")
    else:
        typer.echo(f"Ошибка: {result.get('message', 'Unknown error')}")


@app.command()
def status():
    """Показать статус системы"""
    from src.core.database import db
    from src.services.queue_manager import RabbitMQManager
    
    async def get_status():
        await db.create_tables()
        
        # Статистика БД
        vacancies = await db.get_all_vacancies()
        unprocessed = await db.get_unprocessed_vacancies()
        with_letters = await db.get_vacancies_with_cover_letters()
        applied = [v for v in vacancies if v.applied]
        
        # Статистика очередей
        rabbitmq = RabbitMQManager()
        queue_stats = {}
        if await rabbitmq.connect():
            queue_stats = await rabbitmq.get_queue_stats()
            await rabbitmq.close()
        
        return {
            'vacancies_total': len(vacancies),
            'vacancies_unprocessed': len(unprocessed),
            'vacancies_with_letters': len(with_letters),
            'vacancies_applied': len(applied),
            'queue_vacancies': queue_stats.get(settings.QUEUE_VACANCIES, 0),
            'queue_letters': queue_stats.get(settings.QUEUE_COVER_LETTERS, 0)
        }
    
    stats = asyncio.run(get_status())
    
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    table = Table(title="Статус системы")
    table.add_column("Метрика", style="cyan")
    table.add_column("Значение", style="green")
    
    table.add_row("Всего вакансий", str(stats['vacancies_total']))
    table.add_row("Необработанных", str(stats['vacancies_unprocessed']))
    table.add_row("С письмами", str(stats['vacancies_with_letters']))
    table.add_row("Отправленных", str(stats['vacancies_applied']))
    table.add_row("Очередь вакансий", str(stats['queue_vacancies']))
    table.add_row("Очередь писем", str(stats['queue_letters']))
    
    console.print(table)


@app.command()
def auth():
    """Настройка авторизации HH.ru"""
    typer.echo("🔐 Запуск настройки авторизации HH.ru...")
    from src.api.hh_auth import main as auth_main
    asyncio.run(auth_main())


def main():
    """Точка входа приложения"""
    app()


if __name__ == "__main__":
    main()
