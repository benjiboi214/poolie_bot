import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from models import User, Competition
from db_util import DatabaseManager
from playhouse.shortcuts import model_to_dict
import requests

def create_competition(event, context):
    print("create_competition: Receieved event - ", event)

    user, created = User.get_or_create(
        slack_id=event['slack_event']['profile']['id'],
        username=event['slack_event']['profile']['name'],
        name=event['slack_event']['profile']['real_name']
    )

    if created:
        print("user created")
    else:
        print("user found")
    print("create_competition: User found - ", model_to_dict(user))

    competition = Competition.select().where(
        (Competition.channel == event['slack_event']['event']['channel']) &
        (Competition.status != Competition.FINISHED)
    ).first()

    if not competition:
        competition = Competition.create(
            channel=event['slack_event']['event']['channel'],
            status=Competition.NEW,
            admin=user
        )
        print("Competition created: ", model_to_dict(competition))
        message = {
            "destination": user.slack_id,
            "text": "Are you sure you want to create a competition?",
            "attachments": [
                {
                    "text": "Confirm to open Registration, Cancel to remove the Competition",
                    "fallback": "Something went wrong, delete the competition and try again.",
                    "callback_id": "poolie_confim_competition",
                    "color": "#3ab503",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "confirm",
                            "text": "Confirm",
                            "type": "button",
                            "value": "confirm",
                            "style": "good"
                        },
                        {
                            "name": "cancel",
                            "text": "Cancel",
                            "type": "button",
                            "value": "cancel",
                            "style": "danger"
                        }
                    ]
                }
            ]
        }
        event['action_event'] = message
    else:
        print("Competition already exists: ", model_to_dict(competition))
        message = {
            "destination": user.slack_id,
            "text": "Competition already exists, fuck off cuck."
        }
        event['action_event'] = message

    return event

def confirm_competition(event, context):
    print("confirm_competition: Receieved event - ", event)
    response_message = event['original_message']
    del response_message['attachments'][0]['actions']
    response_message['attachments'][0]['footer'] = "Your competition has been confirmed, thanks for your response."
    r = requests.post(event['response_url'], data = response_message)
    print(r)
    return event

def cancel_competition(event, context):
    print("cancel_competition: Receieved event - ", event)
    response_message = event['original_message']
    del response_message['attachments'][0]['actions']
    response_message['attachments'][0]['footer'] = "Your competition has been canceled, thanks for your response."
    r = requests.post(event['response_url'], data = response_message)
    print(r)
    return event
