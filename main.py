import sys, asyncio
import os
import logging
import TgBot
from aiohttp import web
from GM import Gmpart
from config import *

from aiogoogle import Aiogoogle

app = web.Application()


async def index_html(request: web.Request):
    return web.FileResponse('./index.html')


async def bot_handler(request: web.Request):
    """Will be handling webhooks to bot
    """

    Lewis.Dispatcher.set_current(Lewis.dp)
    Lewis.Bot.set_current(Lewis.dp.bot)
    try:
        await Lewis.dp.updates_handler.notify(
            Lewis.types.Update(**(await request.json())))
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
        # returned_state = request.query['state'][0]
        # Check state
        # TODO: uncomment and check states in DB to connect accout to chat
        # if returned_state != state:
        #     raise ServerError('NO')
        await gmpart_api.build_user_creds(request.rel_url.query.get('code'))
        # TODO: delete link from chat
        msgs = await gmpart_api.messages_list(3)
        for msg in msgs:
            store_attachments(msg)

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
            print("Don't know how to display {}".format(richest.get_content_type()))
    for part in msg.iter_attachments():
        fn = part.get_filename()
        if fn:
            extension = os.path.splitext(part.get_filename())[1]
        else:
            extension = mimetypes.guess_extension(part.get_content_type())
        with open(os.path.splitext(part.get_filename())[0]+extension, 'wb') as f:
            f.write(part.get_content())


async def app_on_startup(app):
    TgBot.filters.setup(dp)
    TgBot.middlewares.setup(dp)

    from TgBot.utils.notify_admins import on_startup_notify
    await on_startup_notify(dp)
    await dp.bot.set_webhook(TgBot.data.config.WEBHOOK_URL)


async def app_on_cleanup(app):
    await dp.bot.delete_webhook()
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
    from TgBot.handlers import dp

    app.add_routes(server_routes)
    app.on_startup.append(app_on_startup)
    app.on_cleanup.append(app_on_cleanup)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
