import asyncio
from aiohttp import web
from config import *
from GM import Gmpart
from DB import PostgreSQL
import TgBot
from TgBot.handlers import dp
from TgBot.utils.notify_admins import on_startup_notify
from TgBot.utils.notify_admins import on_shutdown_notify
from TgBot.loader import current_states
from TgBot.loader import Bot, Dispatcher, types


app = web.Application()
gmpart_api = Gmpart(CLIENT_CREDS)
TgBot.filters.setup(dp)
TgBot.middlewares.setup(dp)

"""a bit unvertain about that
uses low-level API of asyncio
this loop also uses in main file"""
loop = asyncio.get_event_loop()
psqldb = loop.run_until_complete(PostgreSQL.DataBase().connect(DATABASE_URL))
