import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from handlers import polls, goals, megakopilka, admin, top, cups, events, broadcast
from utils.scheduler import schedule_daily_poll

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Реєстрація роутерів
    dp.include_router(polls.router)
    dp.include_router(goals.router)
    dp.include_router(megakopilka.router)
    dp.include_router(top.router)
    dp.include_router(cups.router)
    dp.include_router(events.router)
    dp.include_router(broadcast.router)
    dp.include_router(admin.router)

    # Планувальник щоденного опитування о 13:00
    scheduler = AsyncIOScheduler(timezone="Europe/Kiev")
    schedule_daily_poll(scheduler, bot)
    scheduler.start()

    logger.info("🎮 Brawl Stars Club Bot запущено!")

    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
