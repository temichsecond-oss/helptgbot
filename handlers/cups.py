import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, GROUP_CHAT_ID
from utils.publish import publish_keyboard

router = Router()
CUPS_FILE = "data/cups.json"


def load_cups() -> dict:
    if not os.path.exists(CUPS_FILE):
        return {"personal": {}}
    with open(CUPS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("personal", {})
    return data


def save_cups(data: dict):
    os.makedirs(os.path.dirname(CUPS_FILE), exist_ok=True)
    with open(CUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cups_text() -> str:
    data = load_cups()
    personal = data.get("personal", {})
    if not personal:
        return "🏆 <b>Рекорди кубків клубу</b>\n\nЩе немає рекордів."
    sorted_members = sorted(personal.items(), key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>Рекорди кубків клубу</b>\n\n"
    for i, (name, cups) in enumerate(sorted_members, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        text += f"{medal} <b>{name}</b> — {cups:,} 🏆\n"
    return text


@router.message(Command("cups"))
async def cmd_cups(message: Message):
    await message.reply(cups_text(), parse_mode="HTML")


@router.message(Command("addrecord"))
async def cmd_add_record(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть додавати рекорди.")
        return
    args = message.text.split()
    if len(args) < 3:
        await message.reply(
            "❌ Формат: <code>/addrecord Ім'я Кількість</code>\n"
            "Приклад: <code>/addrecord Дмитро 25000</code>",
            parse_mode="HTML"
        )
        return
    try:
        cups = int(args[-1])
        name = " ".join(args[1:-1])
    except ValueError:
        await message.reply("❌ Кількість кубків має бути числом.")
        return

    data = load_cups()
    old_record = data["personal"].get(name, 0)
    is_new = cups > old_record
    data["personal"][name] = cups
    save_cups(data)

    record_badge = "🏆 <b>НОВИЙ РЕКОРД!</b>\n\n" if is_new else ""
    improve = f"\n📈 Покращено на {cups - old_record:,} кубків!" if is_new and old_record > 0 else ""

    await message.reply(
        f"{record_badge}👤 <b>{name}</b>\n🏆 Кубків: <b>{cups:,}</b>{improve}\n\nОпублікувати таблицю рекордів у групу?",
        parse_mode="HTML",
        reply_markup=publish_keyboard("cups")
    )


@router.callback_query(F.data == "pub_yes_cups")
async def publish_cups(callback: CallbackQuery):
    await callback.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=cups_text(),
        parse_mode="HTML"
    )
    await callback.message.edit_text("✅ Рекорди опубліковано у групу!")
    await callback.answer()


@router.callback_query(F.data == "pub_no_cups")
async def no_publish_cups(callback: CallbackQuery):
    await callback.message.edit_text("👌 Збережено, не опубліковано.")
    await callback.answer()


@router.message(Command("mycups"))
async def cmd_my_cups(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Формат: <code>/mycups Ім'я</code>", parse_mode="HTML")
        return
    name = args[1].strip()
    data = load_cups()
    cups = data["personal"].get(name)
    if cups is None:
        await message.reply(f"❌ Учасника <b>{name}</b> не знайдено.", parse_mode="HTML")
        return
    await message.reply(f"👤 <b>{name}</b>\n🏆 Рекорд: <b>{cups:,}</b> кубків", parse_mode="HTML")
