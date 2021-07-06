from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def make_emails_keyboard(emails):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=email)] for email in emails
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
