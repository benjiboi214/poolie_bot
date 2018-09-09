import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

import json
import boto3
client = boto3.client('stepfunctions')

from urllib.parse import parse_qs
from slackclient import SlackClient
from peewee import IntegrityError


def handle_message(event, context):
    print("handle_message: Receieved event - ", event)

    data = json.loads(event['body'])
    print("handle_message: event body is - ", data)
    return_body = "{}"

    if 'type' in data and data["type"] == "url_verification":
        print("Received challenge")
        return_body = data["challenge"]
    else:
        event = { "slack_event": data }  # Structure event so namespace is preserved
        response = client.start_execution(
            stateMachineArn=os.environ['statemachine_arn'],
            input=json.dumps(event))
        print("handle_message: Triggered step function: ", response)

    return {
        "statusCode": 200,
        "body": return_body
    }

def handle_action(event, context):
    print("handle_action: Receieved event - ", event)

    action_payload = json.loads(parse_qs(event['body'])['payload'][0])
    action_payload['action'] = action_payload['callback_id'] + '_' + action_payload['actions'][0]['name']

    print("handle_action: Parsed event payload - ", action_payload)

    response = client.start_execution(
            stateMachineArn=os.environ['statemachine_arn'],
            input=json.dumps(action_payload))

    print("handle_action: Triggered state machine - ", action_payload)

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

def generate_button_attachment(text, action, style, value):
    return {
        "name": action,
        "text": text,
        "type": "button",
        "value": value,
        "style": style
    }

def get_user_profile(event, context):
    print("get_user_profile: Receieved event - ", event)

    token = os.environ['slack_token']
    sc = SlackClient(token)
    response = sc.api_call(
        "users.info",
        user=event['slack_event']['event']['user'])
    event['slack_profile'] = response['user']
    return event



    #     with DatabaseManager()as db_connection:
    #         try:
    #             with db_connection.atomic():
    #                 SlackEvent.create(event_id=data['event']['client_msg_id'])
    #             import boto3
    #             client = boto3.client('stepfunctions')
    #             response = client.start_execution(
    #                 stateMachineArn=os.environ['statemachine_arn'],
    #                 input=json.dumps(data))
    #         except IntegrityError:
    #             print("Event Already processed. Not running statemachine")