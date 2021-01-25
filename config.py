import os
import sys

DEBUG = sys.argv[1:] == ['DEBUG']
if DEBUG:
    from dotenv import load_dotenv
    load_dotenv()


client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT')

HOST = os.getenv('HOST')
WEBHOOK_PATH = "/webhook/lewis/"
WEBHOOK_URL = f"{HOST}{WEBHOOK_PATH}"

# Telegram admins
admins = [
    os.getenv("ADMIN_ID"),
]
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))

DATABASE_URL = os.getenv('DATABASE_URL')

CLIENT_CREDS = {
    "client_id": client_id,
    "client_secret": client_secret,
    "scopes": ['https://www.googleapis.com/auth/gmail.readonly'],
    "redirect_uri": HOST + "/callback/aiogoogle",
}
DB_IP = os.getenv("DB_IP")

if DEBUG:
    CLIENT_CREDS["redirect_uri"] = \
        HOST + ":" + WEBAPP_PORT + "/callback/aiogoogle"
