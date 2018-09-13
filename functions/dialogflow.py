import os
import string
import sys
from random import choice
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from botocore.vendored import requests

allchar = string.ascii_letters + string.punctuation + string.digits

def parse_message(event, context):
    print("parse_message: Receieved event - ", event)

    sessionId = "".join(choice(allchar) for x in range(36))
    query = event['slack_event']['event']['text']
    payload = {
        "v": "20150910",
        "lang": "en",
        "sessionId": sessionId,
        "query": query
    }
    headers = {"Authorization": "Bearer " + os.environ['dialog_access_token']}
    r = requests.get('https://api.dialogflow.com/v1/query', params=payload, headers=headers)
    response_json = r.json()
    print("Recieved Response: ", response_json)

    event["dialogflow_event"] = {
        "sessionId": sessionId,
        "query": query,
        "action": response_json['result']['action'],
        "response": response_json['result']['fulfillment']['speech']
    }
    return event
