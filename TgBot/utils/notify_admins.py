import logging

from aiogram import Dispatcher

from TgBot.data.config import admins


async def on_startup_notify(dp: Dispatcher):
    for admin in admins:
        try:
            await dp.bot.send_message(admin, "Я працюю!")

        except Exception as err:
            logging.exception(err)


async def on_shutdown_notify(dp: Dispatcher):
    for admin in admins:
        try:
            await dp.bot.send_message(admin, "Я завершую роботу!")

        except Exception as err:
            logging.exception(err)
