import os, sys

if sys.argv[1:] == ['DEBUG']:
    from dotenv import load_dotenv
    load_dotenv()


client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT')

CLIENT_CREDS = {
    "client_id": client_id,
    "client_secret": client_secret,
    "scopes": ['https://www.googleapis.com/auth/gmail.readonly'],
    "redirect_uri": "https://lewis-bots.herokuapp.com/callback/aiogoogle",
}