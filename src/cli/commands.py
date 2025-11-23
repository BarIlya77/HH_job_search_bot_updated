# src/cli/commands.py
import typer

app = typer.Typer()

@app.command()
def worker():
    """Запуск воркера обработки"""
    from src.workers.vacancy_worker import main
    import asyncio
    asyncio.run(main())

@app.command()
def search():
    """Поиск новых вакансий"""
    from src.services.vacancy_searcher import search_new_vacancies
    import asyncio
    asyncio.run(search_new_vacancies())

@app.command()
def status():
    """Показать статус"""
    from src.cli.utils import show_status
    import asyncio
    asyncio.run(show_status())