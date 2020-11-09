import logging

from aiogram import Dispatcher

from config import admins


async def admins_notify(dp: Dispatcher, text="Я працюю!"):
    for admin in admins:
        try:
            await dp.bot.send_message(admin, text, disable_notification=True)

        except Exception as err:
            logging.exception(err)
