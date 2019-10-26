from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json
import base64

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

def save_json(name, obj):
    with open(name+".json", "w") as file:
        json.dump(obj, file, indent=4, sort_keys=True)


def get_attachment_by_id(service, user_id, msg_id, att_id):
    return service.users().messages().attachments().get(userId=user_id, messageId=msg_id,id=att_id).execute()["data"]


def save_attachment(path, data):
    with open(path, 'wb') as f:
        f.write(file_data)

# proces the parts
def parce_payload(message_payload, message_id):
    # chek if it has nested parts
    if message_payload["mimeType"][:9] == "multipart":
        return [parce_payload(part, message_id) for part in message_payload["parts"]]
    elif "body" in message_payload:
        # check if there any attachment
        if message_payload["filename"]:
            if "data" in message_payload["body"]:
                data = message_payload["body"]["data"]
                return {"data":data}
            else:
                attachment_id = message_payload["body"]["attachmentId"]
                return {"file":
                    {"attachment_id":attachment_id,
                    "filename":message_payload["filename"]}}
        # elif message_payload['mimeType'] == 'text/plain':
        elif message_payload['mimeType'][:4] == 'text':
            # make smth with parts like 0.1 0.2 (same body in html/text and plain/text)
            body_decoded = base64.urlsafe_b64decode(message_payload['body']['data']).decode('UTF-8')
            return {"message_body":body_decoded}


def parse_message_object(message_object):
    return parce_payload(message_object["payload"], message_object["id"])


def main():
   
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))
    
    # Call the Gmail API to fetch INBOX
    n_msg_to_show = 1;
    results = service.users().messages().list(userId='me', 
            labelIds=['INBOX'], 
            includeSpamTrash=True, 
            maxResults=n_msg_to_show).execute()
    message_objects = [service.users().messages().get(userId='me', 
        id=message['id']).execute() for message in results.get('messages', [])]
    if not message_objects:
        print("No messages found.")
    else:
        messages = [parse_message_object(message_object) for message_object in message_objects]
        save_json("last_message.json", messages[0])

if __name__ == '__main__':
    main()