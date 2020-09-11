import sys
import os
import logging
import TgBot
from aiohttp import web
from GM import Gmpart
from DB import PostgreSQL
from TgBot.loader import current_states


DEBUG = sys.argv[1:] == ['DEBUG']
BOT_ID = None
app = web.Application()


async def index_html(request: web.Request):
    return web.FileResponse('html/index.html')


async def answers_html(request: web.Request):
    return web.FileResponse('html/answers.html')


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
        logging.info(error)
        return web.json_response(error)
    elif request.rel_url.query.get('code'):
        gmpart_api = Gmpart(CLIENT_CREDS)
        returned_state = request.query['state']
        if returned_state not in current_states.keys():
            return web.Response(text="Wrong EMAIL")
        user_creds = await gmpart_api.build_user_creds(request.rel_url.query.get('code'))
        logging.info(user_creds)
        email = await gmpart_api.get_email_address(user_creds)
        chat_id = current_states[returned_state]['chat_id']
        chat_type = current_states[returned_state]['chat_type']
        logging.info(f"{email = }")
        logging.info(f"{chat_id = }")
        logging.info(f"{chat_type = }")
        if current_states[returned_state]['email'] != email:
            return web.Response(text="Emails doesn't match")
        else:
            global psqldb
            await psqldb.add_chat(chat_id=chat_id, chat_type=chat_type)
            await psqldb.add_gmail(
                email=email,
                refresh_token=user_creds['refresh_token'],
                access_token=user_creds['access_token'],
                expires_at=user_creds['expires_at'],
                chat_id=chat_id
            )
            await dp.bot.send_message(
                chat_id,
                f"Пошта {email} додана до чату")
        raise web.HTTPFound(location='https://t.me/lewis_msg_bot')
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
    """
    Work before server startup
    Parameters:
    app (aiohttp.web.Application: current server app
    """
    TgBot.filters.setup(dp)
    TgBot.middlewares.setup(dp)

    from TgBot.utils.notify_admins import on_startup_notify
    await on_startup_notify(dp)
    BOT_ID = (await dp.bot.me).id
    await dp.bot.set_webhook(WEBHOOK_URL)
    global psqldb
    psqldb = await PostgreSQL.DataBase().connect()
    await psqldb.create_db()


async def app_on_cleanup(app):
    """
    Graceful shutdown work
    Parameters:
    app (aiohttp.web.Application: current server app
    """
    """
    Bad idea because it cancels ability
    to wake up server via webhook i.e. telegram message
    await dp.bot.delete_webhook()
    """
    from TgBot.utils.notify_admins import on_shutdown_notify
    await on_shutdown_notify(dp)
    await dp.bot.close()


server_routes = [
    web.get('/', index_html),
    web.get('/answers', answers_html),
    web.post(path=WEBHOOK_PATH, handler=bot_handler),
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
        # Ability to test only bot via long polling
        # need Upgrade
        TgBot.filters.setup(dp)
        TgBot.middlewares.setup(dp)
        from aiogram import executor
        executor.start_polling(dp, on_shutdown=app_on_cleanup)

    else:
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
