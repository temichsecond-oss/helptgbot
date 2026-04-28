from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS, GROUP_CHAT_ID

router = Router()

# Тимчасове сховище між FSM і callback
_pending_say: dict = {}


def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📢 Відправити", callback_data=f"send_yes_{action}"),
        InlineKeyboardButton(text="❌ Скасувати", callback_data=f"send_no_{action}"),
    ]])


# ──────────────────────────────────────────
#  /say — текст або фото у групу
# ──────────────────────────────────────────

class SayStates(StatesGroup):
    waiting_for_content = State()


@router.message(Command("say"))
async def cmd_say(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори.")
        return
    await message.reply(
        "✍️ <b>Повідомлення у групу</b>\n\n"
        "Надішліть текст <b>або картинку</b> (можна з підписом) — бот відправить це у групу:",
        parse_mode="HTML"
    )
    await state.set_state(SayStates.waiting_for_content)


@router.message(SayStates.waiting_for_content, F.photo)
async def say_photo_received(message: Message, state: FSMContext):
    """Отримали фото."""
    await state.clear()

    caption = message.caption or ""
    photo_id = message.photo[-1].file_id  # найбільша якість

    _pending_say[message.from_user.id] = {
        "type": "photo",
        "photo_id": photo_id,
        "caption": caption,
    }

    preview_caption = f"\n📝 Підпис: <i>{caption}</i>" if caption else "\n📝 Підпис: <i>немає</i>"
    await message.reply(
        f"🖼 <b>Попередній перегляд:</b>{preview_caption}\n\n―――――――――\nВідправити фото у групу?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard("say")
    )


@router.message(SayStates.waiting_for_content, F.text)
async def say_text_received(message: Message, state: FSMContext):
    """Отримали текст."""
    await state.clear()

    _pending_say[message.from_user.id] = {
        "type": "text",
        "text": message.text,
    }

    await message.reply(
        f"📋 <b>Попередній перегляд:</b>\n\n{message.text}\n\n―――――――――\nВідправити у групу?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard("say")
    )


@router.callback_query(F.data == "send_yes_say")
async def confirm_say(callback: CallbackQuery):
    data = _pending_say.pop(callback.from_user.id, None)
    if not data:
        await callback.answer("❌ Дані не знайдено, спробуй ще раз.", show_alert=True)
        return

    if data["type"] == "photo":
        await callback.bot.send_photo(
            chat_id=GROUP_CHAT_ID,
            photo=data["photo_id"],
            caption=data["caption"] or None,
        )
    else:
        await callback.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=data["text"],
        )

    await callback.message.edit_text("✅ Відправлено у групу!")
    await callback.answer()


@router.callback_query(F.data == "send_no_say")
async def cancel_say(callback: CallbackQuery):
    _pending_say.pop(callback.from_user.id, None)
    await callback.message.edit_text("❌ Відправку скасовано.")
    await callback.answer()


# ──────────────────────────────────────────
#  /rickroll — Rick Roll для клубу 🎉
# ──────────────────────────────────────────

RICKROLL_TEXT = (
    "🎮 <b>УВАГА! ТЕРМІНОВЕ ПОВІДОМЛЕННЯ ДЛЯ КЛУБУ!</b>\n\n"
    "🏆 Розробники Brawl Stars щойно оголосили:\n\n"
    "✅ Безкоштовний Chaos Drop\n"
    "✅ x2 Star Drop\n"
    "👇 Скануй QR-код щоб забрати бонуси! 👇"
)


@router.message(Command("rickroll"))
async def cmd_rickroll(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Тільки адміністратори.")
        return
    await message.reply(
        "🎣 <b>Rick Roll для клубу</b>\n\n"
        "Бот відправить повідомлення з QR-кодом на «бонуси» 😈\n\n"
        "Відправити у групу?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard("rickroll")
    )


@router.callback_query(F.data == "send_yes_rickroll")
async def confirm_rickroll(callback: CallbackQuery):
    try:
        photo = FSInputFile("qr_code.png")
        await callback.bot.send_photo(
            chat_id=GROUP_CHAT_ID,
            photo=photo,
            caption=RICKROLL_TEXT,
            parse_mode="HTML"
        )
        await callback.message.edit_text("😂 Rick Roll з QR-кодом відправлено! 🎣")
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Помилка: переконайся що файл <code>qr_code.png</code> лежить у папці з ботом.\n\n{e}",
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data == "send_no_rickroll")
async def cancel_rickroll(callback: CallbackQuery):
    await callback.message.edit_text("😅 Зберіг сюрприз на потім!")
    await callback.answer()
