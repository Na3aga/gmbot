from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command
from TgBot.loader import dp
from TgBot.utils.misc import rate_limit
from TgBot.utils import chat_emails_keyboard
from TgBot.states.stop_watch import StopWatchGmail

from loader import gmail_API, psqldb
from re import match
import logging

@rate_limit(5, 'stop_watch')
@dp.message_handler(Command('stop_watch'), state=None)
async def stop_watch_email(message: types.Message):
    """
    Stop watchin updates for this email
    """
    text = 'Надішліть у відповідь вашу електронну пошту, з якої ' \
           'більше не бажаєте отримувати нові листи в цей чат (тільки GMail)'
    await message.answer(text, reply_markup=await chat_emails_keyboard(message.chat.id))

    await StopWatchGmail.Remove.set()

@dp.message_handler(state=StopWatchGmail.Remove)
async def remove(message: types.Message, state: FSMContext):
    email = message.text.strip()
    chat_id = message.chat.id
    if not match(r'^[\w\.-]+@gmail\.com$', email):
        logging.info(f"Mail {email} was rejected")
        await message.answer('Невідомий формат пошти',
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        await psqldb.remove_watched_chat_emails(email=email, chat_id=chat_id)
        await message.answer(f'Сповіщення від пошти {email} відключені')
        watched_chats = tuple(await psqldb.get_watched_chats(email=email))
        if not watched_chats:
            creds = tuple(await psqldb.get_gmail_creds(email=email))
            user_creds = gmail_API.make_user_creds(*creds)
            await gmail_API.stop_watch(
                user_creds=user_creds,
                email=email)
            await psqldb.remove_watched_email(email=email)
    await state.finish()