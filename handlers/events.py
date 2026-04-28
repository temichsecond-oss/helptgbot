import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS, GROUP_CHAT_ID
from utils.publish import publish_keyboard

router = Router()

EVENTS_FILE = "data/events.json"

EVENT_TYPES = {
    "mega": "💰 Мегакопілка",
    "season": "🗓️ Новий сезон",
    "brawlpass": "🎫 Brawl Pass",
    "tournament": "🏟️ Турнір",
    "special": "⭐ Спеціальна подія",
    "other": "📌 Інше",
}


# ──────────────────────────────────────────
#  Утиліти
# ──────────────────────────────────────────

def load_events() -> list:
    if not os.path.exists(EVENTS_FILE):
        return []
    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(events: list):
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def events_text() -> str:
    events = load_events()
    if not events:
        return "📅 <b>Розклад подій Brawl Stars</b>\n\nПодій поки немає."
    text = "📅 <b>Розклад подій Brawl Stars</b>\n\n"
    for event in events:
        type_label = EVENT_TYPES.get(event.get("type", "other"), "📌")
        text += f"{type_label} <b>{event['title']}</b>\n"
        text += f"   📆 {event['date']}\n"
        if event.get("description"):
            text += f"   💬 {event['description']}\n"
        text += "\n"
    return text


# ──────────────────────────────────────────
#  FSM
# ──────────────────────────────────────────

class EventStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_type = State()
    waiting_for_description = State()


# ──────────────────────────────────────────
#  Команди
# ──────────────────────────────────────────

@router.message(Command("addevent"))
async def cmd_add_event(message: Message, state: FSMContext):
    """Додати подію до розкладу."""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть додавати події.")
        return

    await message.reply(
        "📅 <b>Нова подія</b>\n\nВведіть назву події:",
        parse_mode="HTML"
    )
    await state.set_state(EventStates.waiting_for_title)


@router.message(EventStates.waiting_for_title)
async def event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.reply(
        "📆 Введіть дату події у форматі <code>ДД.ММ.РРРР</code>\n"
        "Або <code>ДД.ММ.РРРР - ДД.ММ.РРРР</code> для діапазону:",
        parse_mode="HTML"
    )
    await state.set_state(EventStates.waiting_for_date)


@router.message(EventStates.waiting_for_date)
async def event_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)

    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"etype_{key}")]
        for key, label in EVENT_TYPES.items()
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply("🏷️ Оберіть тип події:", reply_markup=kb)
    await state.set_state(EventStates.waiting_for_type)


@router.callback_query(F.data.startswith("etype_"))
async def event_type(callback: CallbackQuery, state: FSMContext):
    etype = callback.data.split("_", 1)[1]
    await state.update_data(type=etype)
    await callback.message.edit_text(
        f"✅ Тип: <b>{EVENT_TYPES[etype]}</b>\n\n"
        "📝 Введіть опис події (або <code>-</code> щоб пропустити):",
        parse_mode="HTML"
    )
    await state.set_state(EventStates.waiting_for_description)


@router.message(EventStates.waiting_for_description)
async def event_description(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    description = "" if message.text == "-" else message.text
    events = load_events()
    events.append({
        "id": len(events) + 1,
        "title": data["title"],
        "date": data["date"],
        "type": data["type"],
        "description": description
    })
    save_events(events)

    type_label = EVENT_TYPES.get(data["type"], "📌")
    await message.reply(
        f"✅ Подію збережено!\n\n"
        f"{type_label} <b>{data['title']}</b>\n"
        f"📅 {data['date']}\n\nОпублікувати розклад подій у групу?",
        parse_mode="HTML",
        reply_markup=publish_keyboard("events")
    )


@router.message(Command("events"))
async def cmd_events(message: Message):
    await message.reply(events_text(), parse_mode="HTML")


@router.callback_query(F.data == "pub_yes_events")
async def publish_events(callback: CallbackQuery):
    await callback.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=events_text(),
        parse_mode="HTML"
    )
    await callback.message.edit_text("✅ Розклад опубліковано у групу!")
    await callback.answer()


@router.callback_query(F.data == "pub_no_events")
async def no_publish_events(callback: CallbackQuery):
    await callback.message.edit_text("👌 Збережено, не опубліковано.")
    await callback.answer()


@router.message(Command("delevent"))
async def cmd_del_event(message: Message):
    """Видалити подію зі списку."""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори.")
        return

    events = load_events()
    if not events:
        await message.reply("❌ Немає подій для видалення.")
        return

    buttons = [
        [InlineKeyboardButton(
            text=f"{EVENT_TYPES.get(e.get('type','other'), '📌')} {e['title']} ({e['date']})",
            callback_data=f"delevent_{e['id']}"
        )]
        for e in events
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply("Оберіть подію для видалення:", reply_markup=kb)


@router.callback_query(F.data.startswith("delevent_"))
async def del_event_callback(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    events = load_events()
    events = [e for e in events if e["id"] != event_id]
    save_events(events)
    await callback.message.edit_text("🗑️ Подію видалено!")
    await callback.answer()
