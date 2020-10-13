from aiogram import types
from aiogram.dispatcher.filters.builtin import Command
from aiogram.types.input_file import InputFile
from TgBot.loader import dp
from TgBot.utils.misc import rate_limit
from loader import gmail_API, psqldb
from io import BytesIO


@rate_limit(5, 'last')
@dp.message_handler(Command('last'))
async def last_email(message: types.Message):
    """
    Handle command such as `/last email@gmail.com`
    Send user text and attachment from last email from that email
    """
    # a lot of bugs here
    args = message.get_args()
    # yeah it need at least some verification
    email = args
    creds = tuple(await psqldb.get_gmail_creds(email=email))
    user_creds = gmail_API.make_user_creds(*creds)
    messages = await gmail_API.messages_list(
        user_creds=user_creds,
        messages_num=1,
    )
    messages = [gmail_API.get_text_attachments(msg) for msg in messages]
    for msg in messages:
        await message.answer(msg['text'])
        for file in msg['attachments']:
            await message.answer_document(
                InputFile(
                    BytesIO(file['file']),
                    filename=file['filename']
                )
            )
    del messages
