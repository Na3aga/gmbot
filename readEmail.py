from __future__ import print_function
import pickle
import os.path
import json
import base64
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# get ready to authenticate without specific file but with id and secrets
with open('credentials.json') as file_stream:
    credentials = json.load(file_stream)

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        # Also we can re-authenticate without user if token expires
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # use 'credentials' var instead of 'credentials.json' file
            flow = Flow.from_client_config(
                credentials,
                scopes=SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')

            # Tell the user to go to the authorization URL.
            auth_url, _ = flow.authorization_url(prompt='consent')
            print('Please go to this URL: {}'.format(auth_url))
            # The user will get an authorization code. This code is used to get the
            # access token.
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    # Call the Gmail API
    # show last 5 labels from inbox
    messages_to_show = 5
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])


if __name__ == '__main__':
    main()