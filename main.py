import logging
from aiohttp import web
from TgBot.loader import Bot, Dispatcher, types
from TgBot import dp
from TgBot.utils.notify_admins import admins_notify
from loader import (current_states,
                    gmail_API,
                    psqldb,
                    WEBHOOK_URL,
                    WEBHOOK_PATH,
                    WEBAPP_HOST,
                    WEBAPP_PORT,
                    DEBUG,
                    GMAIL_PUSH_PATH)


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


async def gmail_pubsub_push(request: web.Request):
    """Will be handling webhooks from gmail
    """
    logging.info(str(await request.json()))
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
        returned_state = request.query['state']
        if returned_state not in current_states.keys():
            return web.Response(text="Wrong EMAIL")
        user_creds = await gmail_API.build_user_creds(
            request.rel_url.query.get('code')
        )
        logging.debug(user_creds)
        email = await gmail_API.get_email_address(user_creds=user_creds)
        chat_id = current_states[returned_state]['chat_id']
        chat_type = current_states[returned_state]['chat_type']
        logging.info(f"{email = }")
        logging.info(f"{chat_id = }")
        logging.info(f"{chat_type = }")
        if current_states[returned_state]['email'] != email:
            return web.Response(text="Emails doesn't match")
        else:
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


async def app_on_startup(app):
    """
    Work before server startup
    Parameters:
    app (aiohttp.web.Application: current server app
    """
    from TgBot import filters, middlewares
    filters.setup(dp)
    middlewares.setup(dp)
    await admins_notify(dp, text="Я працюю!")
    await dp.bot.set_webhook(WEBHOOK_URL)


async def app_testing_startup(app):
    """
    Same as app_on_startup(app)
    """
    from TgBot import filters, middlewares
    filters.setup(dp)
    middlewares.setup(dp)
    await admins_notify(dp, text="Я починаю тестування!")


async def app_on_cleanup(app):
    """
    Graceful shutdown work
    Parameters:
    app (aiohttp.web.Application: current server app
    """
    """
    Do not delete_webhook, this is a bad idea because it cancels ability
    to wake up server via webhook i.e. telegram message if it sleeps
    await dp.bot.delete_webhook()
    """
    await admins_notify(dp, text="Я завершую роботу!")
    await dp.bot.close()


async def app_testing_cleanup(app):
    """
    Same as app_on_cleanup(app)
    """
    await admins_notify(dp, text="Я завершую тестування!")
    await dp.bot.close()


server_routes = [
    web.get('/', index_html),
    web.get('/answers', answers_html),
    web.post(path=WEBHOOK_PATH, handler=bot_handler),
    web.post(path=GMAIL_PUSH_PATH, handler=gmail_pubsub_push),
    web.get(path='/callback/aiogoogle', handler=gauthorize_callback)]

# On startup server
# https://docs.aiohttp.org/en/stable/web_advanced.html#background-tasks

# Close webhooks on shutdown
# https://docs.aiohttp.org/en/stable/web_advanced.html#graceful-shutdown

if __name__ == '__main__':
    # one and the only dispatcher

    app.add_routes(server_routes)
    # Bot, Dispatcher is used for webhook setting

    if DEBUG:
        # Ability to test only bot via long polling
        # need Upgrade
        from aiogram import executor
        executor.start_polling(
            dp,
            on_startup=app_testing_startup,
            on_shutdown=app_testing_cleanup
        )
        """
        Only on testing, polling runs it's own infinite loop
        I don't want to make own executor or do smth with
        dispatcher so I decided to run bot, then on Ctrl+C
        web server runs.
        """
    else:
        app.on_startup.append(app_on_startup)
        app.on_cleanup.append(app_on_cleanup)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
