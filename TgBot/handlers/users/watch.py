from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command
from TgBot.loader import dp
from TgBot.utils.misc import rate_limit
from TgBot.states.watch import WatchGmail

from loader import gmail_API, psqldb
from re import match
import logging


@rate_limit(5, 'watch')
@dp.message_handler(Command('watch'), state=None)
async def start_watch_email(message: types.Message):
    """
    Add email to watch its updates
    """
    text = 'Надішліть у відповідь вашу електронну пошту, з якої ' \
           'бажаєте отримувати нові листи (тільки GMail)'
    await message.answer(text)

    await WatchGmail.Add.set()


@dp.message_handler(state=WatchGmail.Add)
async def add(message: types.Message, state: FSMContext):
    email = message.text.strip()
    chat_id = message.chat.id
    if not match(r'^[\w\.-]+@gmail\.com$', email):
        logging.info(f"Mail {email} was rejected")
        await message.answer('Невідомий формат пошти')
    else:
        # TODO: check if that email is attached to the chat
        match_email_chat = await psqldb.email_in_chat(email=email,
                                                      chat_id=chat_id)
        if not match_email_chat:
            await message.answer(f'Пошта {email} не додана до чату')
        else:
            # TODO: if so -- add to the watchlist to handle new emails
            await psqldb.add_watched_chat_emails(email=email, chat_id=chat_id)
            is_email_watched = await psqldb.email_watched(email=email)
            # TODO: if email already watched -- just add to the chat, not watch
            if not is_email_watched:
                creds = tuple(await psqldb.get_gmail_creds(email=email))
                user_creds = gmail_API.make_user_creds(*creds)
                watch_response = await gmail_API.start_watch(
                    user_creds=user_creds,
                    email=email)
                logging.info(str(watch_response))
                if watch_response:
                    await psqldb.watch_email(email=email)
                    await message.answer(f'Пошта {email} додана до чату')
                else:
                    await message.answer(f'Проблеми з додаванням пошти')
            else:
                await message.answer(f'Пошта {email} додана до чату')
    await state.finish()
