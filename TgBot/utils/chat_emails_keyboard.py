from loader import psqldb
from TgBot.keyboards.default import make_emails_keyboard

async def chat_emails_keyboard(chat_id: int):
    email_records = await psqldb.get_chat_emails(chat_id=chat_id)
    return make_emails_keyboard(rec["email"] for rec in email_records)
