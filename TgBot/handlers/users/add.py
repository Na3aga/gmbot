from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command

from TgBot.loader import dp
from TgBot.utils.misc import rate_limit
from TgBot.states.add import AddGmail
from TgBot.keyboards.inline.account_check import check_markup

from main import Gmpart, CLIENT_CREDS, current_states
from re import match
import logging


@rate_limit(5, 'add')
@dp.message_handler(Command('add'), state=None)
async def start_gmail_add(message: types.Message):
    text = 'Надішліть вашу електронну адресу у відповідь на це повідомлення '\
        '(тільки GMail)'
    await message.answer(text)

    await AddGmail.Add.set()


@dp.message_handler(state=AddGmail.Add)
async def add(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if match(r'^[\w\.-]+@gmail\.com$', email):
        await message.answer('Невідомий формат пошти')
        await state.finish()
        return
    gmpart_api = Gmpart(CLIENT_CREDS)
    state_account = gmpart_api.state
    chat_id = message.chat.id
    auth_uri = gmpart_api.authorize_uri(email)
    text = 'Надайте доступ до читання повідомлень вашої пошти ' + auth_uri
    logging.info(f"{auth_uri = }")
    await message.answer(text, reply_markup=check_markup(state_account))
    current_states.update(
        {state_account:
            {'chat_id': chat_id,
             'email': email}})
    await AddGmail.AccountCheck.set()


@dp.callback_query_handler(
    text_contains="connect_gmail",
    state=AddGmail.AccountCheck
)
async def check_processing(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=3)
    logging.info(f"{call.data}")
    _, state_account = call.data.split(':')
    if current_states.get(state_account):
        await call.answer(
            "Авторизуйтесь за посиланням в повідомленні вище",
            show_alert=True
        )
        return
    await call.answer(
        "GMail додано до чату",
        show_alert=True
    )
    current_states.pop(state_account)
    call.message.edit_reply_markup(None)
    await state.finish()


@dp.callback_query_handler(text_contains="cancel", state=AddGmail.AccountCheck)
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=3)
    logging.info(f"{call.data}")
    _, state_account = call.data.split(':')
    await call.answer(
        "Скасування авторизації",
        show_alert=True
    )
    current_states.pop(state_account)
    call.message.edit_reply_markup(None)
    await state.finish()
