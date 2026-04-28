import json
import os
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS, GROUP_CHAT_ID

router = Router()

GOALS_FILE = "data/goals.json"


def load_goals() -> list:
    if not os.path.exists(GOALS_FILE):
        return []
    with open(GOALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_goals(goals: list):
    os.makedirs(os.path.dirname(GOALS_FILE), exist_ok=True)
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)


def goals_text(goals: list) -> str:
    text = "🎯 <b>Цілі клубу Brawl Stars</b>\n\n"
    for i, goal in enumerate(goals, 1):
        status = "✅" if goal.get("completed") else "🔄"
        text += f"{status} <b>{i}. {goal['title']}</b>\n"
        if goal.get("description"):
            text += f"   └ {goal['description']}\n"
        text += "\n"
    return text


def publish_kb(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Опублікувати у групу", callback_data=f"{prefix}_yes"),
        InlineKeyboardButton(text="❌ Скасувати", callback_data=f"{prefix}_no"),
    ]])


class GoalStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    confirm_publish = State()


@router.message(Command("goals"))
async def cmd_goals(message: Message):
    goals = load_goals()
    if not goals:
        await message.reply(
            "🎯 <b>Цілі клубу</b>\n\nЦілей ще немає. Адміністратор може додати ціль командою /addgoal",
            parse_mode="HTML"
        )
        return
    await message.reply(goals_text(goals), parse_mode="HTML")


@router.message(Command("addgoal"))
async def cmd_add_goal(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть додавати цілі.")
        return

    await message.reply("🎯 <b>Нова ціль клубу</b>\n\nВведіть назву цілі:", parse_mode="HTML")
    await state.set_state(GoalStates.waiting_for_title)


@router.message(GoalStates.waiting_for_title)
async def goal_title_received(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.reply(
        "📝 Введіть опис цілі (або надішліть <code>-</code> щоб пропустити):",
        parse_mode="HTML"
    )
    await state.set_state(GoalStates.waiting_for_description)


@router.message(GoalStates.waiting_for_description)
async def goal_description_received(message: Message, state: FSMContext):
    data = await state.get_data()
    description = "" if message.text == "-" else message.text
    await state.update_data(description=description)

    desc_line = f"\n   └ {description}" if description else ""
    await message.reply(
        f"📋 <b>Перегляд цілі:</b>\n\n"
        f"🎯 <b>{data['title']}</b>{desc_line}\n\n"
        f"Публікуємо у групу?",
        parse_mode="HTML",
        reply_markup=publish_kb("goal")
    )
    await state.set_state(GoalStates.confirm_publish)


@router.callback_query(F.data == "goal_yes", GoalStates.confirm_publish)
async def goal_publish_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    goals = load_goals()
    new_goal = {
        "id": len(goals) + 1,
        "title": data["title"],
        "description": data.get("description", ""),
        "completed": False
    }
    goals.append(new_goal)
    save_goals(goals)

    await callback.message.edit_text(
        f"✅ Ціль <b>«{data['title']}»</b> збережена!", parse_mode="HTML", reply_markup=None
    )
    await callback.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=goals_text(goals),
        parse_mode="HTML"
    )
    await callback.answer("📢 Опубліковано у групу!")


@router.callback_query(F.data == "goal_no", GoalStates.confirm_publish)
async def goal_publish_no(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    goals = load_goals()
    new_goal = {
        "id": len(goals) + 1,
        "title": data["title"],
        "description": data.get("description", ""),
        "completed": False
    }
    goals.append(new_goal)
    save_goals(goals)

    await callback.message.edit_text(
        f"✅ Ціль <b>«{data['title']}»</b> збережена (без публікації).",
        parse_mode="HTML", reply_markup=None
    )
    await callback.answer()


@router.message(Command("completegoal"))
async def cmd_complete_goal(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть змінювати цілі.")
        return

    goals = load_goals()
    if not goals:
        await message.reply("❌ Немає цілей для виконання.")
        return

    buttons = []
    for goal in goals:
        if not goal.get("completed"):
            buttons.append([InlineKeyboardButton(
                text=f"🎯 {goal['title']}",
                callback_data=f"complete_goal_{goal['id']}"
            )])

    if not buttons:
        await message.reply("✅ Всі цілі вже виконані!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply("Оберіть ціль, яку позначити як виконану:", reply_markup=kb)


@router.callback_query(F.data.startswith("complete_goal_"))
async def complete_goal_callback(callback: CallbackQuery):
    goal_id = int(callback.data.split("_")[-1])
    goals = load_goals()

    completed_goal = None
    for goal in goals:
        if goal["id"] == goal_id:
            goal["completed"] = True
            completed_goal = goal
            break

    save_goals(goals)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📢 Повідомити групу", callback_data=f"notify_goal_{goal_id}"),
        InlineKeyboardButton(text="❌ Не повідомляти", callback_data="notify_goal_skip"),
    ]])

    await callback.message.edit_text(
        f"🏆 Ціль <b>«{completed_goal['title']}»</b> виконана!\n\nПовідомити групу?",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer("✅ Ціль виконана!")


@router.callback_query(F.data.startswith("notify_goal_"))
async def notify_goal_callback(callback: CallbackQuery):
    suffix = callback.data.split("notify_goal_")[1]

    if suffix == "skip":
        await callback.message.edit_text("✅ Групу не повідомлено.", reply_markup=None)
        await callback.answer()
        return

    goal_id = int(suffix)
    goals = load_goals()
    goal = next((g for g in goals if g["id"] == goal_id), None)

    if goal:
        await callback.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"🏆 <b>Ціль виконана!</b>\n\n🎯 <b>{goal['title']}</b>\n\nВітаємо клуб! 💪🔥",
            parse_mode="HTML"
        )

    await callback.message.edit_text("📢 Групу повідомлено!", reply_markup=None)
    await callback.answer()


@router.message(Command("cleargoals"))
async def cmd_clear_goals(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори.")
        return

    goals = [g for g in load_goals() if not g.get("completed")]
    save_goals(goals)
    await message.reply("🗑️ Виконані цілі видалено!")
