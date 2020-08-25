import sys, os, json
import asyncio
from GM import Gmpart
from sanic import Sanic, response
from sanic.exceptions import ServerError
from config import TEST_CLIENT_CREDS, TEST_EMAIL

from aiogoogle import Aiogoogle

test_user_creds = {"access_token":"ya29.a0AfH6SMDgfx7hu0tMtbSBIYr92yqp4AWVSwa9TEhDM-81ier34dYnd3gFC0l_ihYbAAdK1UM6zq9Ibp2RyNAJxr2ZJk6ebzGPspMiWokT-BtBegWblrayZIUKi3JoEsOxRXzLuweVkjxO3KzyzdhQuBovJfjTCBaLhBg","refresh_token":"1//0cu1M5II2GlC_CgYIARAAGAwSNwF-L9IrfKciXIEawE8-fQN7nEZCKog4mQHl2XM2sooHwbmMsvYNrkTttDjVWIc5KN9AbVi4mHI","expires_in":3599,"expires_at":"2020-08-25T16:21:24.080087","scopes":["https://www.googleapis.com/auth/gmail.readonly"],"id_token":"null","id_token_jwt":"null","token_type":"Bearer","token_uri":"https://oauth2.googleapis.com/token","token_info_uri":"https://www.googleapis.com/oauth2/v4/tokeninfo","revoke_uri":"https://oauth2.googleapis.com/revoke"}

LOCAL_ADDRESS = "localhost"
LOCAL_PORT = "5000"

app = Sanic(__name__)
        
#----------------------------------------#
#                                        #
# **Step A (Check OAuth2 figure above)** #
#                                        #
#----------------------------------------#

# Will be done in Bot

# @app.route('/authorize')
# def authorize(request):
#     uri = aiogoogle.oauth2.authorization_url(
#         client_creds=CLIENT_CREDS, state=state, access_type='offline', include_granted_scopes=True, login_hint=EMAIL, prompt='select_account'
#     )
#     # Step A
#     return response.redirect(uri)

#----------------------------------------------#
#                                              #
# **Step B (Check OAuth2 figure above)**       #
#                                              #
#----------------------------------------------#
# NOTE:                                        #
#  you should now be authorizing your app @    #
#   https://accounts.google.com/o/oauth2/      #
#----------------------------------------------#

#----------------------------------------------#
#                                              #
# **Step C, D & E (Check OAuth2 figure above)**#
#                                              #
#----------------------------------------------#

# Step C
# Google should redirect current_user to
# this endpoint with a grant code
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
        # Step D & E (D send grant code, E receive token info)
        full_user_creds = await gmpart_api.aiogoogle.oauth2.build_user_creds(
            grant = request.args.get('code'),
            client_creds = gmpart_api.CLIENT_CREDS
        )
        print(gmpart_api)
        gmpart_api.init_entry_point(full_user_creds)
        # TODO: delete link from chat
        return response.json(full_user_creds)
    else:
        # Should either receive a code or an error
        return response.text("Something's probably wrong with your callback")

async def messages_list():
    async with Aiogoogle(client_creds = TEST_CLIENT_CREDS, user_creds = test_user_creds) as gmpart:
        gmpart_api = await gmpart.discover('gmail', 'v1')
        messages = await gmpart.as_user(
            gmpart_api.users.messages.list(
                userId='me', 
                labelIds='INBOX', 
                includeSpamTrash=True, 
                maxResults=5)
            )
    print(messages)
if __name__ == '__main__':
    # gmpart_api = Gmpart(TEST_CLIENT_CREDS)
    # print(gmpart_api.authorize_uri('TEST_EMAIL'))
    # app.run(host=LOCAL_ADDRESS, port=LOCAL_PORT, debug=True)
    # print('@@ After server run')
    asyncio.run(messages_list())


        
