from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
from utils.scheduler import update_poll_time, load_poll_time

router = Router()


@router.message(Command("start", "help"))
async def cmd_help(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    hour, minute = load_poll_time()
    base_text = (
        "🎮 <b>Помічник клубу Brawl Stars</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>ОПИТУВАННЯ</b>\n"
        "/newpoll — створити нове опитування 🔒\n"
        f"/setpolltime — змінити час авто-опитування (зараз {hour:02d}:{minute:02d}) 🔒\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>ЦІЛІ КЛУБУ</b>\n"
        "/goals — переглянути цілі клубу\n"
        "/addgoal — додати нову ціль 🔒\n"
        "/completegoal — позначити ціль виконаною 🔒\n"
        "/cleargoals — видалити виконані цілі 🔒\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>МЕГАКОПІЛКА</b>\n"
        "/megastart [назва] — почати мегакопілку 🔒\n"
        "/megaend — завершити мегакопілку 🔒\n"
        "/megastatus — статус і список учасників\n"
        "/megahistory — історія мегакопілок\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>ТОП АКТИВНОСТІ</b>\n"
        "/top — топ активних учасників\n"
        "/addpoints Ім'я 10 — додати очки 🔒\n"
        "/removepoints Ім'я 5 — зняти очки 🔒\n"
        "/resetpoints — скинути таблицю 🔒\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 <b>РЕКОРДИ КУБКІВ</b>\n"
        "/cups — таблиця рекордів клубу\n"
        "/addrecord Ім'я 25000 — додати рекорд 🔒\n"
        "/mycups Ім'я — рекорд учасника\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📅 <b>ПОДІЇ Brawl Stars</b>\n"
        "/events — розклад подій\n"
        "/addevent — додати подію 🔒\n"
        "/delevent — видалити подію 🔒\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📣 <b>ПОВІДОМЛЕННЯ</b>\n"
        "/say — відправити повідомлення від бота 🔒\n"
        "/rickroll — 🎣 сюрприз для клубу 🔒\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔒 — тільки для адміністраторів"
    )

    if is_admin:
        base_text += "\n\n👑 <i>Ви маєте права адміністратора.</i>"

    await message.reply(base_text, parse_mode="HTML")


@router.message(Command("setpolltime"))
async def cmd_set_poll_time(message: Message):
    """/setpolltime 15:00 — змінити час щоденного опитування"""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори.")
        return

    args = message.text.split()
    if len(args) < 2:
        hour, minute = load_poll_time()
        await message.reply(
            f"⏰ Поточний час опитування: <b>{hour:02d}:{minute:02d}</b>\n\n"
            "Щоб змінити: <code>/setpolltime 15:00</code>",
            parse_mode="HTML"
        )
        return

    try:
        time_str = args[1]
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, AttributeError):
        await message.reply("❌ Невірний формат. Приклад: <code>/setpolltime 15:00</code>", parse_mode="HTML")
        return

    success = update_poll_time(message.bot, hour, minute)
    if success:
        await message.reply(
            f"✅ Час щоденного опитування змінено на <b>{hour:02d}:{minute:02d}</b> (Київ) 🕐",
            parse_mode="HTML"
        )
    else:
        await message.reply("❌ Помилка оновлення. Спробуй перезапустити бота.")


@router.message(Command("adminlist"))
async def cmd_admin_list(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки для адміністраторів.")
        return
    ids_str = "\n".join(f"• <code>{aid}</code>" for aid in ADMIN_IDS)
    await message.reply(
        f"👑 <b>Адміністратори бота:</b>\n{ids_str}",
        parse_mode="HTML"
    )
