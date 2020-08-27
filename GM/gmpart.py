import logging
import asyncio
from aiogoogle import Aiogoogle
from aiogoogle.auth.utils import create_secret
from email import policy
from email.parser import BytesParser
from base64 import urlsafe_b64decode


class Gmpart():
    # TODO: save user_creds on exit from with
    # : try wrap all request to `async with as` in decorator
    def __init__(self, CLIENT_CREDS, user_creds = None):
        """Init class with basic parameters
        Parameters:
        CLIENT_CREDS (dict): Your client credentials from google api in format
        TEST_CLIENT_CREDS = {
            "client_id": '',
            "client_secret": '',
            "scopes": ['https://www.googleapis.com/auth/gmail.readonly'],
            "redirect_uri": "",
        }
        """
        self.CLIENT_CREDS = CLIENT_CREDS
        self.user_creds = user_creds
        self.state = create_secret()
        self.gmpart_api = None

    def authorize_uri(self, email):
        """ Generate authozisation uri via aiogoogle's oauth wrapper
        Parameters:
        email (str): IDK some login_hint
        """
        aiogoogle = Aiogoogle(client_creds = self.CLIENT_CREDS)
        if aiogoogle.oauth2.is_ready(self.CLIENT_CREDS):
            uri = aiogoogle.oauth2.authorization_url(
                client_creds=self.CLIENT_CREDS,
                state=self.state,
                access_type='offline',
                include_granted_scopes=True,
                login_hint=email,
                prompt='select_account',
            )
        else:
            raise ServerError("Client doesn't have enough info for Oauth2")
        return uri

    async def build_user_creds(self, code):
        async with Aiogoogle(client_creds = self.CLIENT_CREDS) as aiogoogle:
            self.user_creds = await aiogoogle.oauth2.build_user_creds(
                grant = code,
                client_creds = self.CLIENT_CREDS
            )

    def update_access_token(self, user_creds):
        self.user_creds['access_token'] = user_creds['access_token']
        self.user_creds['expires_in'] = user_creds['expires_in']
        self.user_creds['expires_at'] = user_creds['expires_at']

        # remember, that aiogoogle has it's own Auth manager
        # so you don't need to refresh tocken by hand

    async def create_api(self):
        async with Aiogoogle(client_creds = self.CLIENT_CREDS) as aiogoogle:
            # Downloads the API specs and creates an API object
            return await aiogoogle.discover('gmail', 'v1')

    async def get_gmail_message(self, id, user_id='me', format = 'RAW'):
        async with Aiogoogle(client_creds = self.CLIENT_CREDS, user_creds = self.user_creds) as aiogoogle:
            gmpart_api = await self.create_api()
            return await aiogoogle.as_user(gmpart_api.users.messages.get(
                            userId = user_id, 
                            id = id, 
                            format = 'RAW'))

    @staticmethod
    async def make_email(future_message):
        """ Make email from future base64 encoded raw message
        Parameters:
        future_message (coroutine): base64 encoded raw message
            (maybe RFC 2822)
        """
        return BytesParser(policy=policy.default
            ).parsebytes(urlsafe_b64decode((await future_message)['raw']))

    async def messages_list(self, messages_num = 5):
        """ Get last messages_num emails as email.message object
        Parameters:
        messages_num (int): numbers of messages to be returned
        """
        async with Aiogoogle(client_creds = self.CLIENT_CREDS, user_creds = self.user_creds) as aiogoogle:
            if not self.gmpart_api:
                self.gmpart_api = await self.create_api()
            messages_ids = await aiogoogle.as_user(
                self.gmpart_api.users.messages.list(
                    userId='me', 
                    labelIds='INBOX',
                    includeSpamTrash=True, 
                    maxResults=messages_num)
                )
            raw_messages = []
            for message in messages_ids['messages']:
                raw_messages.append(self.get_gmail_message(message['id']))
            messages = []
            for m in raw_messages:
                # is there blocking?
                messages.append(await self.make_email(m))
            # TODO: find a way not to write this in the every `with as`
            self.update_access_token(aiogoogle.user_creds)
        return messages

