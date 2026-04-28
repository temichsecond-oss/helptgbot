import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_IDS, GROUP_CHAT_ID

router = Router()

KYIV_TZ = ZoneInfo("Europe/Kiev")


def kyiv_now() -> str:
    return datetime.now(KYIV_TZ).strftime("%d.%m.%Y %H:%M")

MEGA_FILE = "data/megakopilka.json"


# ──────────────────────────────────────────
#  Утиліти
# ──────────────────────────────────────────

def load_mega() -> dict:
    if not os.path.exists(MEGA_FILE):
        return {"active": False, "start_date": None, "title": "", "session_id": 0, "participants": [], "participant_names": [], "history": []}
    with open(MEGA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("session_id", 0)
    data.setdefault("participants", [])
    data.setdefault("participant_names", [])
    return data


def save_mega(data: dict):
    os.makedirs(os.path.dirname(MEGA_FILE), exist_ok=True)
    with open(MEGA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────
#  Команди
# ──────────────────────────────────────────

@router.message(Command("megastart"))
async def cmd_mega_start(message: Message):
    """Оголосити початок мегакопілки."""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть запускати мегакопілку.")
        return

    # Отримати назву мегакопілки з аргументу
    args = message.text.split(maxsplit=1)
    title = args[1] if len(args) > 1 else "Мегакопілка"

    data = load_mega()
    if data.get("active"):
        await message.reply(
            f"⚠️ Мегакопілка <b>«{data['title']}»</b> вже активна!\n"
            "Завершіть поточну командою /megaend перед запуском нової.",
            parse_mode="HTML"
        )
        return

    now = kyiv_now()
    data["active"] = True
    data["start_date"] = now
    data["title"] = title
    data["session_id"] = data.get("session_id", 0) + 1
    data["participants"] = []
    data["participant_names"] = []
    data["history"].append({"title": title, "started": now, "ended": None})
    save_mega(data)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏆 Я беру участь!", callback_data="mega_join")
    ]])

    await message.answer(
        f"🚨🚨🚨 <b>МЕГАКОПІЛКА ПОЧАЛАСЬ!</b> 🚨🚨🚨\n\n"
        f"🎮 <b>{title}</b>\n\n"
        f"📅 Початок: {now}\n\n"
        f"💰 Всі учасники клубу — збираємось і фармимо разом!\n"
        f"Натисни кнопку нижче, щоб підтвердити участь 👇",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data == "mega_join")
async def mega_join_callback(callback: CallbackQuery):
    user = callback.from_user
    data = load_mega()

    # Перевіряємо чи вже бере участь у цій мегакопілці
    if user.id in data.get("participants", []):
        await callback.answer(
            "😄 Ти вже берешь участь у цій мегакопілці! Продовжуй фармити 💪",
            show_alert=True
        )
        return

    # Додаємо учасника
    full_name = user.full_name or user.first_name
    username_part = f" (@{user.username})" if user.username else ""
    data["participants"].append(user.id)
    data["participant_names"].append(f"{full_name}{username_part}")
    save_mega(data)
    now = kyiv_now()

    mega_title = data.get("title", "Мегакопілка")

    # Повідомлення для адмінів
    admin_text = (
        f"💰 <b>Новий учасник мегакопілки!</b>\n\n"
        f"👤 <b>{full_name}</b>{username_part}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🎮 Мегакопілка: <b>{mega_title}</b>\n"
        f"🕐 Час: {now}"
    )

    # Розсилаємо кожному адміну особисто
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[WARN] Не вдалось надіслати адміну {admin_id}: {e}")

    await callback.answer(f"🎉 {user.first_name}, ти в грі! Удачі у мегакопілці!", show_alert=True)


@router.message(Command("megaend"))
async def cmd_mega_end(message: Message):
    """Завершити мегакопілку."""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть завершити мегакопілку.")
        return

    data = load_mega()
    if not data.get("active"):
        await message.reply("❌ Зараз немає активної мегакопілки.")
        return

    now = kyiv_now()
    title = data["title"]
    data["active"] = False

    # Оновити запис в історії
    if data["history"]:
        data["history"][-1]["ended"] = now

    save_mega(data)

    await message.answer(
        f"✅ <b>Мегакопілка завершена!</b>\n\n"
        f"🎮 <b>{title}</b>\n"
        f"📅 Завершено: {now}\n\n"
        f"🏆 Дякуємо всім учасникам! Ви найкращий клуб! 💪",
        parse_mode="HTML"
    )


@router.message(Command("megastatus"))
async def cmd_mega_status(message: Message):
    """Перевірити статус мегакопілки."""
    data = load_mega()

    if data.get("active"):
        names = data.get("participant_names", [])
        count = len(names)

        text = (
            f"🔥 <b>МЕГАКОПІЛКА АКТИВНА!</b>\n\n"
            f"🎮 Назва: <b>{data['title']}</b>\n"
            f"📅 Початок: {data['start_date']}\n\n"
        )

        if count == 0:
            text += "👥 Учасників поки немає — будь першим!\n\n"
        else:
            text += f"👥 <b>Учасники ({count}):</b>\n"
            for i, name in enumerate(names, 1):
                text += f"  {i}. {name}\n"
            text += "\n"

        text += "Продовжуємо фармити! 💰"

        await message.reply(text, parse_mode="HTML")
    else:
        history = data.get("history", [])
        last = history[-1] if history else None
        text = "😴 <b>Мегакопілки зараз немає.</b>\n\n"
        if last:
            text += f"🕐 Остання: <b>{last['title']}</b>\n"
            text += f"   Почалась: {last['started']}\n"
            if last.get("ended"):
                text += f"   Завершилась: {last['ended']}\n"
        await message.reply(text, parse_mode="HTML")


@router.message(Command("megahistory"))
async def cmd_mega_history(message: Message):
    """Показати історію мегакопілок."""
    data = load_mega()
    history = data.get("history", [])

    if not history:
        await message.reply("📭 Історія мегакопілок порожня.")
        return

    text = "📜 <b>Історія мегакопілок</b>\n\n"
    for i, entry in enumerate(reversed(history[-10:]), 1):
        status = "✅" if entry.get("ended") else "🔥 активна"
        text += f"{i}. <b>{entry['title']}</b> — {status}\n"
        text += f"   ▶️ {entry['started']}"
        if entry.get("ended"):
            text += f" → {entry['ended']}"
        text += "\n\n"

    await message.reply(text, parse_mode="HTML")
