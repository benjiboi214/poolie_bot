import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

import json
import boto3

from urllib.parse import parse_qs
from slackclient import SlackClient

client = boto3.client('stepfunctions')

def handle_message(event, context):
    print("handle_message: Receieved event - ", event)

    data = json.loads(event['body'])
    print("Got data: {}".format(data))
    return_body = "{}"

    if 'type' in data and data["type"] == "url_verification":
        print("Received challenge")
        return_body = data["challenge"]
    else:
        token = os.environ['slack_token']
        sc = SlackClient(token)
        response = sc.api_call(
            "users.info",
            user=data['event']['user'])
        data['profile'] = response['user']
        response = client.start_execution(
            stateMachineArn=os.environ['statemachine_arn'],
            input=json.dumps(data))

    return {
        "statusCode": 200,
        "body": return_body
    }

def handle_action(event, context):
    print("handle_action: Receieved event - ", event)
    action_payload = json.loads(parse_qs(event['body'])['payload'][0])
    action_payload['action'] = action_payload['callback_id'] + '_' + action_payload['actions'][0]['value']
    print("handle_action: parsed event payload - ", action_payload)

    response = client.start_execution(
            stateMachineArn=os.environ['statemachine_arn'],
            input=json.dumps(action_payload))

    return {
        "statusCode": 200
    }

def send_message(event, context):
    print("send_message: Receieved event - ", event)

    token = os.environ['slack_token']
    sc = SlackClient(token)
    print("Token is: ", token)

    if 'action_event' in event:
        if 'attachments' in event['action_event']:
            sc.api_call(
                "chat.postMessage",
                channel=event['action_event']['destination'],
                text=event['action_event']['text'],
                attachments=event['action_event']['attachments']
            )
        else:
            sc.api_call(
                "chat.postMessage",
                channel=event['action_event']['destination'],
                text=event['action_event']['text']
            )
    else:
        sc.api_call(
            "chat.postMessage",
            channel=event['slack_event']['event']['channel'],
            text=event['dialogflow_event']['response']
        )