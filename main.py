import logging
from io import BytesIO
from aiohttp import web
from TgBot.loader import Bot, Dispatcher, types
from TgBot import dp
from TgBot.utils.notify_admins import admins_notify
from loader import (current_states,
                    gmail_API,
                    psqldb,
                    WEBHOOK_URL,
                    WEBHOOK_PATH,
                    HOST,
                    WEBAPP_HOST,
                    WEBAPP_PORT,
                    DEBUG,
                    GMAIL_PUSH_PATH)
from base64 import urlsafe_b64decode
import json

app = web.Application()


async def index_html(request: web.Request):
    return web.FileResponse('html/index.html')


async def answers_html(request: web.Request):
    return web.FileResponse('html/answers.html')


async def update_one_watched_email(email):
    logging.info("Updating last_watch: " + email)
    creds = tuple(await psqldb.get_gmail_creds(email=email))
    user_creds = gmail_API.make_user_creds(*creds)
    watch_response = await gmail_API.start_watch(user_creds=user_creds,
                                                 email=email)
    if watch_response:
        await psqldb.watch_email(
            email=email,
            history_id=int(watch_response["historyId"])
        )


async def update_watched_emails():
    await psqldb.apply_old_watched_emails(hours=48,
                                          func=update_one_watched_email)


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
    """
        Handle webhooks from gmail (google pub/sub subscribition)
    """
    MAX_SIZE = 26214400
    if request.content_length > MAX_SIZE:
        raise web.HTTPRequestEntityTooLarge(MAX_SIZE, request.content_length)
    request_data = await request.json()
    logging.info(str(request_data))
    if request_data.get('message'):
        notification_data = request_data['message']['data']
        update = json.loads(
            urlsafe_b64decode(notification_data).decode('utf-8')
        )
        email: str = update["emailAddress"]
        new_history_id: int = int(update["historyId"])
        creds = tuple(await psqldb.get_gmail_creds(email=email))
        user_creds = gmail_API.make_user_creds(*creds)
        history_id = await psqldb.update_watch_history(email=email, history_id=new_history_id)
        if history_id:
            # TODO: Catch 404 and make a full sync in that case
            # https://developers.google.com/gmail/api/guides/sync#full_synchronization
            hist = await gmail_API.read_history(user_creds=user_creds,
                                                email=email,
                                                history_id=str(history_id))
            if hist.get("history"):
                creds = tuple(await psqldb.get_gmail_creds(email=email))
                user_creds = gmail_API.make_user_creds(*creds)
                watched_chats_records = tuple(await psqldb.get_watched_chats(email=email))
                for history_record in hist["history"]:
                    for message_record in history_record["messages"]:
                        message_id = message_record["id"]
                        msg = await gmail_API.get_message_full(
                            user_creds=user_creds,
                            message_id=message_id,
                        )
                        # ON new messages -- send it to all the watched chats linked with this email
                        for chat_id_record in watched_chats_records:
                            for text in msg['text_list']:
                                await dp.bot.send_message(chat_id_record["chat_id"], text)
                            for file in msg['attachments']:
                                await dp.bot.send_document(
                                    chat_id_record["chat_id"],
                                    types.input_file.InputFile(
                                        BytesIO(file['file']),
                                        filename=file['filename']
                                    )
                                )
        else:
            logging.info(f"Problems with updating history_id in {email}")
    return web.Response(text='OK')


async def gauthorize_callback(request: web.Request):
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



async def app_on_startup(app: web.Application):
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
    await update_watched_emails()


async def app_testing_startup(app: web.Application):
    """
    Same as app_on_startup(app)
    """
    from TgBot import filters, middlewares
    filters.setup(dp)
    middlewares.setup(dp)
    await admins_notify(dp, text="Я починаю тестування!")
    await update_watched_emails()
    # WEBAPP DEBUG RUN
    await runner.setup()
    # Host must be without http://
    site = web.TCPSite(runner, "localhost", WEBAPP_PORT)
    await site.start()
    logging.info("App running at " + HOST + ":" + WEBAPP_PORT)



async def app_on_cleanup(app: web.Application):
    """
    Graceful shutdown work
    Parameters:
        app (aiohttp.web.Application): current server app
    """
    """
    Do not delete_webhook, this is a bad idea because it cancels ability
    to wake up server via webhook i.e. telegram message if it sleeps
    await dp.bot.delete_webhook()
    """
    await admins_notify(dp, text="Я завершую роботу!")
    await dp.bot.close()


async def app_testing_cleanup(app: web.Application):
    """
    Same as app_on_cleanup(app)
    """
    await admins_notify(dp, text="Я завершую тестування!")
    await dp.bot.close()
    await runner.cleanup()


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
        from aiogram import executor
        """
        From the inside of an executor
        Same as start_polling but with our web server
        Just use of same server that uses aiogram under the hood
        """
        runner = web.AppRunner(app)

        exec = executor.Executor(
            dp,
            check_ip=False,
        )
        executor._setup_callbacks(exec, app_testing_startup, app_testing_cleanup)
        exec.set_web_app(app)
        exec.start_polling(
            reset_webhook=True,
            timeout=20,
            relax=0.1,
            fast=True,
        )
    else:
        app.on_startup.append(app_on_startup)
        app.on_cleanup.append(app_on_cleanup)
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
