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
        '/help - Список команд',
        '/add - Додати пошту',
        '/remove - Видалити пошту',
        '/watch - Отримувати нові повідомлення з пошти в чат',
        '/stop_watch - Припинити отримувати нові повідомлення з пошти',
    ]
    await message.answer('\n'.join(text))
