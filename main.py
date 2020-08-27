import sys, os, asyncio
from GM import Gmpart
from sanic import Sanic, response
from sanic.exceptions import ServerError
from config import *

from aiogoogle import Aiogoogle


LOCAL_ADDRESS = "localhost"
LOCAL_PORT = "5000"

app = Sanic(__name__)

@app.route('/callback/aiogoogle')
async def callback(request):
    if request.args.get('error'):
        error = {
            'error': request.args.get('error'),
            'error_description': request.args.get('error_description')
        }
        return response.json(error)
    elif request.args.get('code'):
        returned_state = request.args['state'][0]
        # Check state
        # TODO: uncomment and check states in DB to connect accout to chat
        # if returned_state != state:
        #     raise ServerError('NO')
        await gmpart_api.build_user_creds(request.args.get('code'))
        # TODO: delete link from chat
        msgs = await gmpart_api.messages_list(3)
        for msg in msgs:
            store_attachments(msg) 

        print('save user_creds to config.py in order not to confirm app use in google every time')
        print(f'{gmpart_api.user_creds = }')
        return response.json(gmpart_api.user_creds)
    else:
        # Should either receive a code or an error
        return response.text("Something's probably wrong with your callback")

"""Debug save
# Also watch here https://docs.python.org/3/library/email.examples.html
with open(msg['subject']+'.msg', 'wb') as f:
            f.write(bytes(msg))
"""
# from python doc examples
def store_attachments(msg):
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
            # again strip the <> to go from email form of cid to html form.


async def messages_list():
    gm_api = Gmpart(CLIENT_CREDS, user_creds)
    msgs = await gm_api.messages_list(3)
    for msg in msgs:
        store_attachments(msg) 


# Uncomment if:

# This is your first launch
gmpart_api = Gmpart(CLIENT_CREDS)
print(gmpart_api.authorize_uri(EMAIL))
app.run(host=LOCAL_ADDRESS, port=LOCAL_PORT, debug=True)

## You have user_creds in your config
# asyncio.run(messages_list())


        
