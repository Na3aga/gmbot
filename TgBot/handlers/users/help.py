from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from TgBot.loader import dp
from TgBot.utils.misc import rate_limit


@rate_limit(5, 'help')
@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = [
        'Список команд: ',
        '/start - Почати діалог',
        '/help - Список команд'
    ]
    await message.answer('\n'.join(text))
