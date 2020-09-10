import os, sys

if sys.argv[1:] == ['DEBUG']:
    from dotenv import load_dotenv
    load_dotenv()


client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT')

HOST = 'https://lewis-bots.herokuapp.com'
WEBHOOK_PATH = "/api/v1/lewis/webhook/"
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
    "redirect_uri": "https://lewis-bots.herokuapp.com/callback/aiogoogle",
}

DB_IP = os.getenv("DB_IP")
