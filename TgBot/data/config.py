import os
import sys

if sys.argv[1:] == ['DEBUG']:
    from dotenv import load_dotenv
    load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
admins = [
    os.getenv("ADMIN_ID"),
]
DB_IP = os.getenv("DB_IP")

HOST = 'https://lewis-bots.herokuapp.com'
WEBHOOK_PATH = "/api/v1/lewis/webhook/"
WEBHOOK_URL = f"{HOST}{WEBHOOK_PATH}"
