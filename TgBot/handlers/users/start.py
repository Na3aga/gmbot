from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart

from TgBot.loader import dp


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    await message.answer(
    	f'Привіт, {message.from_user.full_name}! '
    	'Я можу пересилати повідомлення з GMail у цей чат. '
    	'Щоб додати пошту натисніть /add та введіть пошту')
