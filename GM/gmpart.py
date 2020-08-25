import logging
from aiogoogle import Aiogoogle
from aiogoogle.auth.utils import create_secret


class Gmpart():
    # TODO: save user_creds in destructor
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
        self.aiogoogle = None
        self.state = create_secret()
        self.init_entry_point(self.user_creds)

    def authorize_uri(self, EMAIL):
        if self.aiogoogle.oauth2.is_ready(self.CLIENT_CREDS):
            uri = self.aiogoogle.oauth2.authorization_url(
                client_creds=self.CLIENT_CREDS,
                state=self.state,
                access_type='offline',
                include_granted_scopes=True,
                login_hint=EMAIL,
                prompt='select_account',
            )
        else:
            raise ServerError("Client doesn't have enough info for Oauth2")
        return uri

    def init_entry_point(self, user_creds):
        self.user_creds = user_creds
        # remember, that aiogoogle has it's own Auth manager
        # so you don't need to refresh tocken by hand
        self.aiogoogle = Aiogoogle(user_creds=self.user_creds, client_creds=self.CLIENT_CREDS)

    async def create_api(self):
        async with self.aiogoogle as aiogoogle:
            # Downloads the API specs and creates an API object
            return await aiogoogle.discover('gmail', 'v1')
