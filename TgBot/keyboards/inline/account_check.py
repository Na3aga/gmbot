from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def check_markup(state_account: str):
    markup = InlineKeyboardMarkup(
        row_width=2
    )
    check_button = InlineKeyboardButton(
        text="З'єднати з GMail",
        callback_data="connect_gmail:" + state_account
    )
    cancel_button = InlineKeyboardButton(
        text="Скасувати",
        callback_data="cancel:" + state_account
    )
    markup.insert(check_button)
    markup.insert(cancel_button)
    return markup
