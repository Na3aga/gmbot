import asyncio
from config import *
from GM import Gmpart
from DB import PostgreSQL


current_states = {}

gmail_API = Gmpart(CLIENT_CREDS)

"""a bit unvertain about that
uses low-level API of asyncio
this loop also uses in main file"""
loop = asyncio.get_event_loop()
psqldb = loop.run_until_complete(PostgreSQL.DataBase().connect(DATABASE_URL))
