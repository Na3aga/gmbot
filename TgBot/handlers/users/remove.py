from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command

from TgBot.loader import dp
from TgBot.utils.misc import rate_limit
from TgBot.states.remove import RemoveGmail
from loader import psqldb
from re import match
import logging

@rate_limit(1, 'remove')
@dp.message_handler(Command('remove'), state=None)
async def start_gmail_add(message: types.Message):
    text = 'Надішліть електронну адресу у відповідь на це повідомлення '\
        'яку бажаєте видалити з чату (тільки GMail)'
    await message.answer(text)
    await RemoveGmail.Remove.set()


@dp.message_handler(state=RemoveGmail.Remove)
async def remove(message: types.Message, state: FSMContext):
    email = message.text.strip()
    chat_id = message.chat.id
    if not match(r'^[\w\.-]+@gmail\.com$', email):
        logging.info(f"Пошта {email} не видалена з чату {chat_id}")
        await message.answer('Невідомий формат пошти')
    else:
        await psqldb.remove_chat_email(email=email, chat_id=chat_id)
        await message.answer(f"Пошта {email} видалена з чату")
        logging.info(f"Пошта {email} видалена з чату {chat_id}")
        email_chats = await psqldb.get_email_chats(email=email)
        if not email_chats:
            await psqldb.remove_email(email=email)
    await state.finish()
