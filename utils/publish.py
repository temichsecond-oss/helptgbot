from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def publish_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавіатура з кнопками Опублікувати / Не публікувати."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📢 Опублікувати у групу", callback_data=f"pub_yes_{action}"),
        InlineKeyboardButton(text="❌ Не публікувати", callback_data=f"pub_no_{action}"),
    ]])
