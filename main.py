import sys, os, json, asyncio
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
        print(await gmpart_api.messages_list())
        print(gmpart_api.user_creds)
        return response.json(gmpart_api.user_creds)
    else:
        # Should either receive a code or an error
        return response.text("Something's probably wrong with your callback")

async def messages_list():
    gm_api = Gmpart(TEST_CLIENT_CREDS, test_user_creds)
    print(await gm_api.messages_list())


if __name__ == '__main__':
    # gmpart_api = Gmpart(TEST_CLIENT_CREDS)
    # print(gmpart_api.authorize_uri('TEST_EMAIL'))
    # app.run(host=LOCAL_ADDRESS, port=LOCAL_PORT, debug=True)
    # print('@@ After server run')
    asyncio.run(messages_list())


        
