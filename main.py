import sys
import asyncio
import os
import logging
from config import *
import TgBot
from aiohttp import web
from aiogoogle import Aiogoogle
from GM import Gmpart
from DB import PostgreSQL

DEBUG = sys.argv[1:] == ['DEBUG']
BOT_ID = None
psqldb = None
app = web.Application()

current_states = {}


async def index_html(request: web.Request):
    return web.FileResponse('html/index.html')


async def bot_handler(request: web.Request):
    """Will be handling webhooks to bot
    """
    Dispatcher.set_current(dp)
    Bot.set_current(dp.bot)
    try:
        await dp.updates_handler.notify(
            types.Update(**(await request.json())))
    except Exception as err:
        logging.error(err)
    finally:
        return web.Response(text='OK')


async def gauthorize_callback(request):
    """Receive user creds from google auth redirect
    """
    # need more tests to find how to catch the error
    if request.rel_url.query.get('error'):
        error = {
            'error': request.rel_url.get('error'),
            'error_description': request.rel_url.query.get('error_description')
        }
        return web.json_response(error)
    elif request.rel_url.query.get('code'):
        gmpart_api = Gmpart(CLIENT_CREDS)
        returned_state = request.query['state'][0]
        # Check state
        # TODO: uncomment and check states in DB to connect accout to chat
        if returned_state not in current_states.keys():
            return web.Response(text="Wrong EMAIL")
        await gmpart_api.build_user_creds(returned_state)
        # + email eq check
        await dp.bot.send_message(
            current_states[returned_state['chat_id']],
            str(user_creds))
        # TODO: delete link from chat
        # msgs = await gmpart_api.messages_list(3)
        # for msg in msgs:
        #     store_attachments(msg)

        print('save user_creds to config.py in order not to confirm app use in google every time')
        print(f'{gmpart_api.user_creds = }')
        return web.json_response(gmpart_api.user_creds)
    else:
        # Should either receive a code or an error
        return web.Response(
            text="Something's probably wrong with your callback")


def store_attachments(msg):
    """Show what can we do with emails
    """
    import mimetypes
    # We can extract the richest alternative in order to display it:
    richest = msg.get_body()
    if richest['content-type'].maintype == 'text':
        if richest['content-type'].subtype == 'plain':
            for line in richest.get_content().splitlines():
                print(line)
        else:
            print("Don't know how to display {}".format(
                richest.get_content_type()))
    for part in msg.iter_attachments():
        fn = part.get_filename()
        if fn:
            extension = os.path.splitext(part.get_filename())[1]
        else:
            extension = mimetypes.guess_extension(part.get_content_type())
        with open(os.path.splitext(part.get_filename())[0] + extension, 'wb') as f:
            f.write(part.get_content())


async def app_on_startup(app):
    TgBot.filters.setup(dp)
    TgBot.middlewares.setup(dp)

    from TgBot.utils.notify_admins import on_startup_notify
    await on_startup_notify(dp)
    BOT_ID = (await dp.bot.me).id
    await dp.bot.set_webhook(TgBot.data.config.WEBHOOK_URL)

    psqldb = await PostgreSQL.DataBase().connect()
    await psqldb.create_db()


async def app_on_cleanup(app):
    # await dp.bot.delete_webhook()
    from TgBot.utils.notify_admins import on_shutdown_notify
    await on_shutdown_notify(dp)
    await dp.bot.close()
""""""

server_routes = [
    web.get('/', index_html),
    web.post(path=TgBot.data.config.WEBHOOK_PATH, handler=bot_handler),
    web.get(path='/callback/aiogoogle', handler=gauthorize_callback)]

# On startup server
# https://docs.aiohttp.org/en/stable/web_advanced.html#background-tasks

# Close webhooks on shutdown
# https://docs.aiohttp.org/en/stable/web_advanced.html#graceful-shutdown

if __name__ == '__main__':
    # one and the only dispatcher
    from TgBot.handlers import dp
    app.add_routes(server_routes)
    app.on_startup.append(app_on_startup)
    app.on_cleanup.append(app_on_cleanup)
    # Bot, Dispatcher is used for webhook setting
    from TgBot.loader import Bot, Dispatcher, types
    if DEBUG:
        TgBot.filters.setup(dp)
        TgBot.middlewares.setup(dp)
        from aiogram import executor
        executor.start_polling(dp, on_shutdown=app_on_cleanup)
    else:
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
