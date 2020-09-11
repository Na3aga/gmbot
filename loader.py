from asyncio import run
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

psqldb = run(PostgreSQL.DataBase().connect())
run(psqldb.create_db())
