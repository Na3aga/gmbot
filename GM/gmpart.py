import logging
import asyncio
from email.message import Message
from typing import cast
from math import ceil
from aiogoogle import Aiogoogle
from email import policy
from email.parser import BytesParser
import email.message
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup, NavigableString, CData, Tag
from html import escape
from loader import GMAIL_PUBSUB_TOPIC_NAME


class TelegramBeautifulSoup(BeautifulSoup):
    """
    Slightly changed parser to preserve telegram-supported tags
    """
    telegram_tags = ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike',
                     'del', 'b', 'i', 's', 'u', 'a', 'a', 'code', 'pre',
                     'pre', 'code']

    def _all_strings(self, strip=False, types=(NavigableString, CData)):
        for descendant in self.descendants:
            # return "a" string representation if we encounter it
            if isinstance(descendant, Tag) and descendant.name in self.telegram_tags:
                yield str(descendant)
            # skip an inner text node inside "a"
            if isinstance(descendant, NavigableString) and descendant.parent.name in self.telegram_tags:
                continue
            # default behavior
            if ((types is None and not isinstance(descendant, NavigableString))
                or
                (types is not None and type(descendant) not in types)):
                continue
            if strip:
                descendant = descendant.strip()
                if len(descendant) == 0:
                    continue
            yield descendant

def aiogoogle_creds(func):
    """
        Add aiogoogle with credentials for every wrapped function

        Warnings:
            Authorisation on every user, IDK can be slow
    """
    # WARNING: only for async functions!
    async def decor(self, *args, **kwargs):
        user_creds = kwargs.get('user_creds')
        async with Aiogoogle(
            client_creds=self.CLIENT_CREDS,
            user_creds=user_creds
        ) as aiogoogle:
            return await func(self, aiogoogle, *args, **kwargs)
    return decor

class Gmpart():
    # TODO: save user_creds on exit from with
    # : try wrap all request to `async with as` in decorator
    # also try catch Bad Request (invalid user creds)

    @classmethod
    def make(cls, CLIENT_CREDS):
        """
        Parameters:
        CLIENT_CREDS (dict): Your client credentials from google api in format
        """
        self = Gmpart()
        self.CLIENT_CREDS = CLIENT_CREDS
        return self

    @aiogoogle_creds
    async def authorize_uri(self, aiogoogle, email, state):
        """ Generate authozisation uri via aiogoogle's oauth wrapper
        Parameters:
        email (str): text will be put into email/username field
        """
        if aiogoogle.oauth2.is_ready(self.CLIENT_CREDS):
            uri = aiogoogle.oauth2.authorization_url(
                client_creds=self.CLIENT_CREDS,
                state=state,
                access_type='offline',
                include_granted_scopes=True,
                login_hint=email,
                prompt='select_account',
            )
        else:
            raise Exception("Client doesn't have enough info for Oauth2")
        return uri

    @aiogoogle_creds
    async def build_user_creds(self, aiogoogle, code):
        """ Get user credentials with refresh token via secret code
        Parameters:
        email (str): IDK some login_hint
        """
        user_creds = await aiogoogle.oauth2.build_user_creds(
            grant=code,
            client_creds=self.CLIENT_CREDS
        )
        return user_creds

    def update_token(self, user_creds):
        # self.user_creds['access_token'] = user_creds['access_token']
        # self.user_creds['expires_in'] = user_creds['expires_in']
        # self.user_creds['expires_at'] = user_creds['expires_at']
        # if user_creds['refresh_token']:
        #     self.user_creds['refresh_token'] = user_creds['refresh_token']
        pass
        # remember, that aiogoogle has it's own Auth manager
        # so you don't need to refresh tocken by hand

    @property
    @aiogoogle_creds
    async def gmpart_api(self, aiogoogle):
        """ Get discover api of gmail.readonly
        """
        # Downloads the API specs and creates an API object
        return await aiogoogle.discover('gmail', 'v1')

    async def get_gmail_message(self, aiogoogle, id, user_creds,
                                user_id='me', format='RAW'):
        """ Ask google for a full message with specific ID

        Parameters:
            id (string): the ID of the message to retrieve.
            user_id (string): the user's email address. The special value `me` can
                be used to indicate the authenticated user.
            format (enum string MINIMAL|FULL|RAW|METADATA): the format
                to return the message in.
        """
        return await aiogoogle.as_user(
            (await self.gmpart_api).users.messages.get(
                userId=user_id,
                id=id,
                format=format
            )
        )

    @staticmethod
    async def make_email(future_message) -> email.message.EmailMessage:
        """ Make email from future base64 encoded raw message

        Parameters:
            future_message (coroutine): base64 encoded raw message
                (maybe RFC 2822 or RFC 822)

        Returns:
            email.message.Message: message in python lib format
        """
        parsed_email: email.message.EmailMessage = cast(
            email.message.EmailMessage,
            BytesParser(
                policy=policy.default
            ).parsebytes(
                urlsafe_b64decode(
                    (await future_message)['raw']
                )
            )
        )
        return parsed_email

    @staticmethod
    def make_user_creds(access_token, refresh_token, expires_at):
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 0000,
            'expires_at': expires_at,
            'scopes': ['https://www.googleapis.com/auth/gmail.readonly'],
            'id_token': None,
            'id_token_jwt': None,
            'token_type': 'Bearer',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'token_info_uri': 'https://www.googleapis.com/oauth2/v4/tokeninfo',
            'revoke_uri': 'https://oauth2.googleapis.com/revoke'
        }

    @staticmethod
    def get_text_attachments(msg, split_size=4096):
        """Get email text in html and attachments
        """
        import mimetypes
        import os
        text = ''
        text += '📨 <b>' + escape(msg['from']) + '</b>\n'
        text += 'Кому: <b>' + escape(msg['to']) + '</b>\n'
        text += 'Тема: <b>' + escape(msg['subject']) + '</b>\n\n'
        attachments = []
        # We can extract the richest alternative in order to display it:
        richest = msg.get_body(preferencelist=('plain', 'html'))
        if richest['content-type'].maintype == 'text':
            if richest['content-type'].subtype == 'plain':
                text += escape(richest.get_content())
            else:
                soup = TelegramBeautifulSoup(richest.get_content(), 'lxml')
                text += soup.body.getText()
                # text += soup.body.getText('\n', strip=True)
        for part in msg.iter_attachments():
            filename = part.get_filename()
            if filename:
                extension = os.path.splitext(part.get_filename())[1]
            else:
                extension = mimetypes.guess_extension(part.get_content_type())
                filename = 'file' + extension
            # with open(os.path.splitext(part.get_filename())[0] + extension, 'wb') as f:
            #     f.write(part.get_content())
            attachments.append({"filename": filename,
                                "file": part.get_content()})
        text_list = []
        if split_size:
            for i in range(ceil(len(text)/split_size)):
                text_list.append(text[split_size*i:split_size*(i+1)])
        else:
            text_list.append(text)

        return {"text_list": text_list,
                "attachments": attachments}

    @aiogoogle_creds
    async def get_message_full(self, aiogoogle, user_creds,
                               message_id: str, user_id: str = 'me'):
        gmail_message = self.get_gmail_message(
            aiogoogle=aiogoogle,
            user_creds=user_creds,
            user_id=user_id,
            id=message_id,
        )
        encoded_message = await self.make_email(gmail_message)
        full_message = self.get_text_attachments(encoded_message)
        return full_message

    @aiogoogle_creds
    async def get_email_address(self, aiogoogle, user_creds):
        """ Get email adress of current account
        Parameters:
        user_creds (dict): user credentials
        """
        profile = await aiogoogle.as_user(
            (await self.gmpart_api).users.getProfile(userId='me')
        )
        return profile['emailAddress']

    @aiogoogle_creds
    async def messages_list(self, aiogoogle, user_creds,
                            messages_num: int = 5):
        """ Get last messages_num emails as email.message object
        Parameters:
            messages_num (int): numbers of messages to be returned

        Returns:
            List[email.message.Message]: List of messages in python email lib
        """
        messages_ids = await aiogoogle.as_user(
            (await self.gmpart_api).users.messages.list(
                userId='me',
                labelIds='INBOX',
                includeSpamTrash=True,
                maxResults=messages_num))
        raw_messages = []
        for message in messages_ids['messages']:
            raw_messages.append(
                self.get_gmail_message(
                    id=message['id'],
                    user_creds=user_creds,
                    aiogoogle=aiogoogle,
                )
            )
        messages = []
        for m in raw_messages:
            # is there blocking?
            messages.append(await self.make_email(m))

        self.update_token(aiogoogle.user_creds)
        return messages

    @aiogoogle_creds
    async def start_watch(self, aiogoogle, user_creds,
                          email):
        """
        Sends watch request
        """
        request_data = {
            "labelIds": ["INBOX"],
            "labelFilterAction": "INCLUDE",
            "topicName": GMAIL_PUBSUB_TOPIC_NAME
        }
        return await aiogoogle.as_user(
            (await self.gmpart_api).users.watch(
                userId=email,
                json=request_data
            )
        )

    @aiogoogle_creds
    async def stop_watch(self, aiogoogle, user_creds,
                         email):
        """
        Stop receiving notifications
        """
        return await aiogoogle.as_user(
            (await self.gmpart_api).users.stop(
                userId=email
            )
        )

    @aiogoogle_creds
    async def read_history(self, aiogoogle, user_creds,
                           email: str,
                           history_id: str,
                           max_results: int = None,
                           label_id: str = "INBOX",
                           history_type: str = "MESSAGE_ADDED"):
        """
        Read events starting from email with history_id
        Args:
            aiogoogle (Aiogoogle): Authorised aiogoogle user
                (with active session)
            user_creds: OAuth2 user credentials (user tokens dict etc.)
            email (str): email which history (new emails) will be read
            history_id (str): id from which new gmail actions will be fetched
            max_results (int): maximum number of new events to fetch
            label_id (str): Label which updates will be watching, one of those
                ["SENT", "INBOX", "IMPORTANT", "TRASH", "DRAFT", "SPAM",
                "CATEGORY_FORUMS", "CATEGORY_UPDATES", "CATEGORY_PERSONAL",
                "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "STARRED", "UNREAD",
                ...] and other user types
            history_type (str): which actions will be watched, can be on of
                [MESSAGE_ADDED, MESSAGE_DELETED, LABEL_ADDED, LABEL_REMOVED]

        Returns:
            : A record of a change to the user's mailbox
        """
        return await aiogoogle.as_user(
            (await self.gmpart_api).users.history.list(
                userId=email,
                maxResults=max_results,
                startHistoryId=history_id,
                labelId=label_id,
                historyTypes=history_type,
            )
        )
