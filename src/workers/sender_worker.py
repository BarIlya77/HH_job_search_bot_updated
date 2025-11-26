import asyncio
import aio_pika
import json
import time
from datetime import datetime
from src.core.database import db
from src.api.hh_responder import HHResponder
from src.services.queue_manager import RabbitMQManager
from src.services.rate_limiter import RateLimiter
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class SenderWorker:
    """Воркер для отправки откликов на HH.ru"""

    def __init__(self):
        self.rabbitmq = RabbitMQManager()
        self.rate_limiter = RateLimiter(settings.REQUESTS_PER_HOUR)
        self.hh_responder = HHResponder()

    async def ask_confirmation(self, cover_data: dict) -> str:
        """Спрашивает подтверждение перед отправкой отклика"""
        print("\n" + "=" * 70)
        print("🎯 НОВЫЙ ОТКЛИК ДЛЯ ОТПРАВКИ")
        print("=" * 70)
        print(f"🏢 Компания: {cover_data['company']}")
        print(f"💼 Вакансия: {cover_data['vacancy_name']}")
        print(f"🔗 Ссылка: {cover_data['url']}")
        print(f"📝 Длина письма: {len(cover_data['cover_letter'])} символов")

        # Показываем время до следующей возможной отправки
        remaining_time = self.rate_limiter.get_remaining_time()
        if remaining_time > 0:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            print(f"⏰ До следующей отправки: {minutes:02d}:{seconds:02d}")

        print("\n📄 СОДЕРЖИМОЕ ПИСЬМА:")
        print("-" * 50)
        print(cover_data['cover_letter'])
        print("-" * 50)

        while True:
            print("\n❓ Выберите действие:")
            print("   [y] - Отправить отклик СЕЙЧАС (без ожидания)")
            print("   [w] - Отправить с ожиданием лимитов")
            print("   [n] - Пропустить вакансию")
            print("   [s] - Пропустить и оставить в очереди")
            print("   [v] - Посмотреть ссылку на вакансию")
            print("   [p] - Показать письмо еще раз")

            choice = input("\nВаш выбор (y/w/n/s/v/p): ").lower().strip()

            if choice in ['y', 'w', 'n', 's']:
                return choice
            elif choice == 'v':
                print(f"🔗 Открываю ссылку: {cover_data['url']}")
                import webbrowser
                webbrowser.open(cover_data['url'])
            elif choice == 'p':
                print("\n📄 СОДЕРЖИМОЕ ПИСЬМА:")
                print("-" * 50)
                print(cover_data['cover_letter'])
                print("-" * 50)
            else:
                print("❌ Неверный выбор, попробуйте еще раз")


    async def process_cover_letter_automatic(self, cover_data: dict) -> bool:
        """Автоматическая отправка без подтверждения"""
        logger.info(f"🎯 АВТОМАТИЧЕСКАЯ ОТПРАВКА")
        logger.info(f"🏢 {cover_data['company']} - {cover_data['vacancy_name']}")
        logger.info(f"🔗 {cover_data['url']}")

        # 🔧 ПРОВЕРКА НА ПРОПУСК
        if await self.should_skip_vacancy(cover_data):
            logger.info("⏩ Вакансия пропущена по правилам")
            return False

        # 🔧 ЗАДЕРЖКА
        logger.info("⏳ Подготовка к отправке...")
        await asyncio.sleep(10)

        await self.rate_limiter.wait_if_needed()

        if await self.should_skip_vacancy(cover_data):
            return False

        # Отправляем отклик
        vacancy_id_str = str(cover_data['vacancy_id']).strip()
        success = await self.hh_responder.send_application(
            vacancy_id_str,
            cover_data['cover_letter']
        )

        if success:
            self.sent_count += 1
            vacancy = await db.get_vacancy_by_hh_id(cover_data['vacancy_id'])
            if vacancy:
                await db.mark_as_applied(vacancy.id)
            logger.info(f"✅ Отклик #{self.sent_count} отправлен")
            return True
        else:
            self.error_count += 1
            logger.error(f"❌ Ошибка отправки (#{self.error_count})")
            return False


    async def process_cover_letter(self, message: aio_pika.IncomingMessage):
        """Обрабатывает сообщение с готовым письмом и отправляет отклик"""
        async with message.process():
            try:
                cover_data = json.loads(message.body.decode('utf-8'))

                # Логируем информацию о вакансии
                logger.info(f"\n📨 Обработка отклика: {cover_data['vacancy_name']}")
                logger.info(f"🏢 Компания: {cover_data['company']}")

                # # Спрашиваем подтверждение
                # choice = await self.ask_confirmation(cover_data)
                if settings.BOT_MODE == "automatic":
                    # АВТОМАТИЧЕСКИЙ РЕЖИМ - отправляем сразу
                    await self.process_cover_letter_automatic(cover_data)
                else:
                    # ИНТЕРАКТИВНЫЙ РЕЖИМ - спрашиваем подтверждение
                    choice = await self.ask_confirmation(cover_data)

                if choice in ['n', 's']:
                    # Если пользователь отказался
                    if choice == 'n':
                        logger.info("🚫 Отклик пропущен и удален из очереди")
                    else:
                        logger.info("⏩ Вакансия оставлена в очереди")
                        # Возвращаем сообщение в очередь
                        await message.nack(requeue=True)
                    return

                # Обработка отправки
                if choice == 'w':
                    # Соблюдаем лимиты HH.ru
                    logger.info("⏳ Ожидание соблюдения лимитов...")
                    await self.rate_limiter.wait_if_needed()
                else:  # choice == 'y'
                    logger.info("🚀 Отправка СЕЙЧАС (без ожидания)")
                    # Сбрасываем таймер для немедленной отправки
                    self.rate_limiter.last_request = 0

                # Отправляем отклик
                vacancy_id_str = str(cover_data['vacancy_id']).strip()
                logger.info("🔄 Отправка отклика...")

                success = await self.hh_responder.send_application(
                    vacancy_id_str,
                    cover_data['cover_letter']
                )

                if success:
                    # ✅ ТОЛЬКО ПРИ УСПЕШНОЙ ОТПРАВКЕ обновляем таймер
                    if choice == 'w':
                        # Для режима с ожиданием таймер уже обновлен в wait_if_needed()
                        pass
                    else:
                        # Для режима "сейчас" обновляем таймер после успешной отправки
                        self.rate_limiter.last_request = time.time()

                    # Помечаем как отправленную в БД
                    vacancy = await db.get_vacancy_by_hh_id(cover_data['vacancy_id'])
                    if vacancy:
                        await db.mark_as_applied(vacancy.id)
                        logger.info(f"✅ Отклик отправлен и записан в БД")
                    else:
                        logger.warning(f"⚠️ Отклик отправлен, но вакансия не найдена в БД")
                else:
                    logger.error(f"❌ Не удалось отправить отклик")
                    # ❌ ПРИ ОШИБКЕ НЕ ОБНОВЛЯЕМ ТАЙМЕР - можно попробовать снова

            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка декодирования JSON: {e}")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки письма: {e}")

    async def main(self):
        """Основная функция воркера"""
        logger.info("🚀 Запуск воркера отправки откликов...")
        logger.info("💡 Режим: ИНТЕРАКТИВНЫЙ (требует подтверждение для каждого отклика)")
        logger.info(f"⚠️  ВНИМАНИЕ: Rate limiting активирован ({settings.REQUESTS_PER_HOUR} откликов/час)")
        logger.info("🎯 Доступные режимы отправки:")
        logger.info("   [y] - СЕЙЧАС (игнорирует лимиты)")
        logger.info("   [w] - С ожиданием (соблюдает лимиты)")

        # Инициализация БД
        await db.create_tables()

        # Подключение к RabbitMQ
        if not await self.rabbitmq.connect():
            logger.error("❌ Не удалось подключиться к RabbitMQ")
            return

        try:
            # Настраиваем канал
            await self.rabbitmq.channel.set_qos(prefetch_count=1)

            # Получаем очередь
            queue = await self.rabbitmq.channel.declare_queue(
                settings.QUEUE_COVER_LETTERS,
                durable=True
            )

            logger.info("✅ Подключение к RabbitMQ установлено")
            logger.info(f"🔄 Ожидание писем в очереди '{settings.QUEUE_COVER_LETTERS}'...")

            # Начинаем слушать очередь
            await queue.consume(self.process_cover_letter)

            logger.info("\n🎯 ВОРКЕР ОТПРАВКИ ЗАПУЩЕН!")
            logger.info("💡 Для каждого отклика будет запрашиваться подтверждение")
            logger.info("⏹️  Нажмите Ctrl+C для остановки")

            # Бесконечное ожидание
            await asyncio.Future()

        except KeyboardInterrupt:
            logger.info("\n🛑 Остановка воркера отправки...")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
        finally:
            await self.rabbitmq.close()


# Функция для запуска
async def main():
    worker = SenderWorker()
    await worker.main()


if __name__ == "__main__":
    asyncio.run(main())
