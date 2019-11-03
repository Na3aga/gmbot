import base64
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json
import base64
from functools import reduce

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

def save_json(file_name, obj):
    with open(file_name+".json", "w") as file:
        json.dump(obj, file, indent=4, sort_keys=True)


def get_attachment_by_id(service, user_id, msg_id, att_id):
    return service.users().messages().attachments().get(userId=user_id, messageId=msg_id,id=att_id).execute()["data"]


def save_attachment(path, data):
    with open(path, 'wb') as f:
        f.write(data)

# proces the parts
def parse_payload(msg_payload):
    # chek if it has nested parts by checking mimeType
    if msg_payload["mimeType"][:9] == "multipart":
        # at first func parse_payload() executes for every part, then they merge into one dict by reduce()
        return reduce(lambda p, nxt_p: {**p, **nxt_p}, map(parse_payload,msg_payload["parts"]))
    elif "body" in msg_payload:
        # check if there is any attachment
        if msg_payload["filename"]:
            if "data" in msg_payload["body"]:
                data = msg_payload["body"]["data"]
                return {msg_payload["filename"]:{"data":data}}
            else:
                attachment_id = msg_payload["body"]["attachmentId"]
                return {msg_payload["filename"]:
                    {"attachment_id":attachment_id}}
        elif msg_payload['mimeType'][:4] == 'text':
            # make smth with parts like 0.1 0.2 (same body in html/text and plain/text)
            body_decoded = base64.urlsafe_b64decode(msg_payload['body']['data']).decode('UTF-8')
            return {msg_payload['mimeType'][5:]:body_decoded}
    return None


def parse_msg_obj(msg_obj):
    return parse_payload(msg_obj["payload"])


def main():
    #Store and retrieve a single credential to and from a file.
    storage = file.Storage('token.json')
    #Gets credentials from storage as oauth2client.client.Credentials
    credentials = storage.get()
    # If there are no (valid) credentials available, let log in from credentials.json
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        credentials = tools.run_flow(flow, storage)

    http = credentials.authorize(Http())
    # func build() Builds client for google services 
    # used params: service(name of service), version, http (authorization)
    service = build('gmail', 'v1', http=http)
    
    # Call the Gmail API to fetch INBOX
    n_msg_to_show = 1;
    results = service.users().messages().list(userId='me', 
            labelIds=['INBOX'], 
            includeSpamTrash=True, 
            maxResults=n_msg_to_show).execute()

    # get whole messages from gmail
    msgs_objects = [service.users().messages().get(userId='me', 
        id=message['id']).execute() for message in results.get('messages', [])]
    if not msgs_objects:
        print("No messages found.")
    else:
        msgs = [parse_msg_obj(msg) for msg in msgs_objects]
        save_json("last_message", msgs[0])

if __name__ == '__main__':
    main()