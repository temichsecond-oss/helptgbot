import json
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import GROUP_CHAT_ID, DAILY_POLL_HOUR, DAILY_POLL_MINUTE

POLL_TIME_FILE = "data/poll_time.json"

DAILY_POLL_QUESTION = "🎮 Чи апнули ви вже за сьогодні 200 кубків??"
DAILY_POLL_OPTIONS = [
    "🚀 Навіть більше 200!",
    "🔥 Так,апнув/апнула",
    "😎 В процесі",
    "😐 Поки що не починав/починала",
]

_scheduler: AsyncIOScheduler = None


def load_poll_time() -> tuple:
    if not os.path.exists(POLL_TIME_FILE):
        return DAILY_POLL_HOUR, DAILY_POLL_MINUTE
    with open(POLL_TIME_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("hour", DAILY_POLL_HOUR), data.get("minute", DAILY_POLL_MINUTE)


def save_poll_time(hour: int, minute: int):
    os.makedirs(os.path.dirname(POLL_TIME_FILE), exist_ok=True)
    with open(POLL_TIME_FILE, "w", encoding="utf-8") as f:
        json.dump({"hour": hour, "minute": minute}, f)


async def send_daily_poll(bot: Bot):
    try:
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text="⏰ <b>Щоденне опитування клубу!</b>",
            parse_mode="HTML"
        )
        await bot.send_poll(
            chat_id=GROUP_CHAT_ID,
            question=DAILY_POLL_QUESTION,
            options=DAILY_POLL_OPTIONS,
            is_anonymous=False,
            allows_multiple_answers=False,
        )
    except Exception as e:
        print(f"[ERROR] Помилка надсилання щоденного опитування: {e}")


def schedule_daily_poll(scheduler: AsyncIOScheduler, bot: Bot):
    global _scheduler
    _scheduler = scheduler
    hour, minute = load_poll_time()
    scheduler.add_job(
        send_daily_poll,
        trigger="cron",
        hour=hour,
        minute=minute,
        timezone="Europe/Kiev",
        args=[bot],
        id="daily_poll",
        replace_existing=True,
    )
    print(f"[SCHEDULER] Щоденне опитування о {hour:02d}:{minute:02d} (Київ) зареєстровано.")


def update_poll_time(bot: Bot, hour: int, minute: int) -> bool:
    global _scheduler
    if _scheduler is None:
        return False
    save_poll_time(hour, minute)
    _scheduler.reschedule_job(
        "daily_poll",
        trigger="cron",
        hour=hour,
        minute=minute,
        timezone="Europe/Kiev",
    )
    print(f"[SCHEDULER] Час опитування змінено на {hour:02d}:{minute:02d} (Київ)")
    return True
