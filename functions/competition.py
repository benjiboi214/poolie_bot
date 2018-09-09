import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from models import User, Competition
from db_util import DatabaseManager
from playhouse.shortcuts import model_to_dict
from slack import generate_button_attachment
import requests

def create_competition(event, context):
    print("create_competition: Receieved event - ", event)

    with DatabaseManager():
        user, created = User.get_or_create(
            slack_id=event['slack_profile']['id'],
            username=event['slack_profile']['name'],
            name=event['slack_profile']['real_name']
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
                        "text": "Confirm or Cancel creation of new Competition",
                        "fallback": "Something went wrong, delete the competition and try again.",
                        "callback_id": "poolie_confim_competition",
                        "color": "#3ab503",
                        "attachment_type": "default",
                        "actions": [
                            generate_button_attachment("Confirm", "confirm", "good", event['slack_event']['event']['channel']),
                            generate_button_attachment("Cancel", "cancel", "danger", event['slack_event']['event']['channel'])
                        ]
                    }
                ]
            }
            event['action_event'] = message
        else:
            print("Competition already exists: ", model_to_dict(competition))
            message = {
                "destination": user.slack_id,
                "text": "Competition already exists."
            }
            event['action_event'] = message

    return event

def confirm_competition(event, context):
    print("confirm_competition: Receieved event - ", event)

    with DatabaseManager():
        user = User.select().where((User.slack_id == event["user"]["id"])).first()
        competition = Competition.select().where(
            (Competition.channel == event['actions'][0]["value"]) &
            (Competition.admin == user)
        ).first()
        competition.status = Competition.REGISTERING
        competition.save()

        print("Found user: ", model_to_dict(user))
        print("Found competition: ", model_to_dict(competition))

        response_message = event['original_message']
        del response_message['attachments'][0]['actions']
        response_message['attachments'][0]['footer'] = "Your competition has been confirmed, thanks for your response."
        print("response is now: ", response_message)
        r = requests.post(event['response_url'], json = response_message)

        message = {
            "destination": competition.channel,
            "text": "Competition has been created by <@{}>. To register, try sending a message in this channel such as:\n '<@UCGV1M7GC> Register me'".format(user.slack_id)
        }
        event['action_event'] = message

    print(r.text)
    return event

def cancel_competition(event, context):
    print("cancel_competition: Receieved event - ", event)

    with DatabaseManager():
        user = User.select().where((User.slack_id == event["user"]["id"])).first()
        competition = Competition.select().where(
            (Competition.channel == event['actions'][0]["value"]) &
            (Competition.admin == user)
        ).first()
        competition.delete_instance()

        print("Found user: ", model_to_dict(user))
        print("Found competition: ", model_to_dict(competition))

        response_message = event['original_message']
        del response_message['attachments'][0]['actions']
        response_message['attachments'][0]['footer'] = "Your competition has been canceled, thanks for your response."
        print("response is now: ", response_message)

        r = requests.post(event['response_url'], json = response_message)

    print(r.text)
    return event
