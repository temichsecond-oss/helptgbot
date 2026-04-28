from aiogram import Router, F
from aiogram.types import Message, PollAnswer
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS

router = Router()


class PollCreation(StatesGroup):
    waiting_for_question = State()
    waiting_for_options = State()


# ──────────────────────────────────────────
#  Команди для адмінів
# ──────────────────────────────────────────

@router.message(Command("newpoll"))
async def cmd_new_poll(message: Message, state: FSMContext):
    """Почати створення нового опитування."""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори можуть створювати опитування.")
        return

    await message.reply(
        "📊 <b>Створення опитування</b>\n\n"
        "Введіть запитання для опитування:",
        parse_mode="HTML"
    )
    await state.set_state(PollCreation.waiting_for_question)


@router.message(PollCreation.waiting_for_question)
async def poll_question_received(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.reply(
        "✅ Запитання збережено!\n\n"
        "Тепер введіть варіанти відповідей — <b>кожен з нового рядка</b> (мінімум 2, максимум 10):",
        parse_mode="HTML"
    )
    await state.set_state(PollCreation.waiting_for_options)


@router.message(PollCreation.waiting_for_options)
async def poll_options_received(message: Message, state: FSMContext):
    options = [line.strip() for line in message.text.split("\n") if line.strip()]

    if len(options) < 2:
        await message.reply("❌ Потрібно мінімум 2 варіанти. Спробуй ще раз:")
        return
    if len(options) > 10:
        await message.reply("❌ Максимум 10 варіантів. Скороти список:")
        return

    data = await state.get_data()
    question = data["question"]
    await state.clear()

    await message.answer_poll(
        question=question,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False,
    )
    await message.reply("🎉 Опитування створено та опубліковано!")


@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    """Логування відповідей на опитування."""
    user = poll_answer.user
    chosen = poll_answer.option_ids
    print(f"[POLL] {user.full_name} обрав варіант(и): {chosen}")
