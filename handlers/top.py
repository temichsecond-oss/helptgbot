import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_IDS, GROUP_CHAT_ID

router = Router()

TOP_FILE = "data/top.json"
MEDALS = ["🥇", "🥈", "🥉"]


def load_top() -> dict:
    if not os.path.exists(TOP_FILE):
        return {}
    with open(TOP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_top(data: dict):
    os.makedirs(os.path.dirname(TOP_FILE), exist_ok=True)
    with open(TOP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def top_text(data: dict) -> str:
    sorted_members = sorted(data.items(), key=lambda x: x[1], reverse=True)
    text = "📊 <b>Топ активних учасників клубу</b>\n\n"
    for i, (name, points) in enumerate(sorted_members[:10], 1):
        medal = MEDALS[i - 1] if i <= 3 else f"{i}."
        text += f"{medal} <b>{name}</b> — {points} очок\n"
    return text


def publish_kb(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Опублікувати у групу", callback_data=f"{prefix}_yes"),
        InlineKeyboardButton(text="❌ Не публікувати", callback_data=f"{prefix}_no"),
    ]])


@router.message(Command("top"))
async def cmd_top(message: Message):
    data = load_top()
    if not data:
        await message.reply(
            "📊 <b>Топ активності клубу</b>\n\nЩе немає даних.\n"
            "Адмін може додати очки командою <code>/addpoints Ім'я 10</code>",
            parse_mode="HTML"
        )
        return
    await message.reply(top_text(data), parse_mode="HTML")


@router.message(Command("addpoints"))
async def cmd_add_points(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть нараховувати очки.")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.reply(
            "❌ Формат: <code>/addpoints Ім'я 10</code>",
            parse_mode="HTML"
        )
        return

    try:
        points = int(args[-1])
        name = " ".join(args[1:-1])
    except ValueError:
        await message.reply("❌ Кількість очок має бути числом.")
        return

    data = load_top()
    if name not in data:
        data[name] = 0
    data[name] += points
    save_top(data)

    kb = publish_kb(f"top_{name}_{points}")
    await message.reply(
        f"✅ <b>{name}</b> отримав(ла) <b>+{points}</b> очок!\n"
        f"Всього: <b>{data[name]}</b> очок 🌟\n\n"
        f"Опублікувати оновлений топ у групу?",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("top_") and F.data.endswith("_yes"))
async def top_publish_yes(callback: CallbackQuery):
    data = load_top()
    await callback.message.edit_text("✅ Публікую топ...", reply_markup=None)
    await callback.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=top_text(data),
        parse_mode="HTML"
    )
    await callback.answer("📢 Топ опубліковано!")


@router.callback_query(F.data.startswith("top_") and F.data.endswith("_no"))
async def top_publish_no(callback: CallbackQuery):
    await callback.message.edit_text(
        callback.message.text.split("\n\nОпублікувати")[0],
        parse_mode="HTML", reply_markup=None
    )
    await callback.answer()


@router.message(Command("removepoints"))
async def cmd_remove_points(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори.")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.reply("❌ Формат: <code>/removepoints Ім'я 5</code>", parse_mode="HTML")
        return

    try:
        points = int(args[-1])
        name = " ".join(args[1:-1])
    except ValueError:
        await message.reply("❌ Кількість очок має бути числом.")
        return

    data = load_top()
    if name not in data:
        await message.reply(f"❌ Учасника <b>{name}</b> не знайдено.", parse_mode="HTML")
        return

    data[name] = max(0, data[name] - points)
    save_top(data)
    await message.reply(
        f"✅ У <b>{name}</b> знято <b>{points}</b> очок. Залишок: <b>{data[name]}</b>",
        parse_mode="HTML"
    )


@router.message(Command("resetpoints"))
async def cmd_reset_points(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори.")
        return
    save_top({})
    await message.reply("🗑️ Таблицю активності скинуто!")
