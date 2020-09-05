from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command

from TgBot.loader import dp
from TgBot.utils.misc import rate_limit
from TgBot.states.add import AddGmail

from main import Gmpart, CLIENT_CREDS, current_states
from re import match
import logging


@rate_limit(1, 'add')
@dp.message_handler(Command('add'), state=None)
async def start_gmail_add(message: types.Message):
    text = 'Надішліть вашу електронну адресу у відповідь на це повідомлення '\
        '(тільки GMail)'
    await message.answer(text)

    await AddGmail.Add.set()


@dp.message_handler(state=AddGmail.Add)
async def add(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if not match(r'^[\w\.-]+@gmail\.com$', email):
        await message.answer('Невідомий формат пошти')
        await state.finish()
        return
    gmpart_api = Gmpart(CLIENT_CREDS)
    state_account = gmpart_api.state
    chat_id = message.chat.id
    auth_uri = gmpart_api.authorize_uri(email)
    text = 'Надайте доступ до читання повідомлень вашої пошти ' + auth_uri
    logging.debug(f"{auth_uri = }"
                  f"{state_account = }"
                  f"{chat_id = }")
    await message.answer(text)
    current_states.update(
        {state_account:
            {'chat_id': chat_id,
             'email': email}})
    await state.finish()
