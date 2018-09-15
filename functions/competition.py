import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

import requests
from playhouse.shortcuts import model_to_dict

from slack import generate_button_attachment

from database.models import Competition, User
from database.util import DatabaseManager
from misc import (get_admin_error_message, get_competition_not_found_message,
                   user_is_admin_of_competition)


def create_competition(event, context):
    print("create_competition: Receieved event - ", event)

    with DatabaseManager("create_competition") as db:
        user, user_created = db.get_or_create_user(
            event['slack_profile']['id'],
            event['slack_profile']['name'],
            event['slack_profile']['real_name'])

        competition, competition_created = db.get_or_create_active_competition(
            event['slack_event']['event']['channel'],
            user)

        if competition_created:
            event['action_event'] = {
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
        else:
            message = {
                "destination": user.slack_id,
                "text": "Competition already exists."
            }
            event['action_event'] = message
    return event

def confirm_competition(event, context):
    print("confirm_competition: Receieved event - ", event)

    with DatabaseManager("confirm_competition") as db:
        user = User.select().where((User.slack_id == event["user"]["id"])).first()
        competition = db.get_active_competition(event['actions'][0]["value"])

        if competition and competition.status == Competition.NEW:
            if user_is_admin_of_competition(user, competition):
                # Update the competition and trigger next action in flow
                competition.status = Competition.REGISTERING
                competition.save()

                response_message = event['original_message']
                del response_message['attachments'][0]['actions']
                response_message['attachments'][0]['footer'] = "Your competition has been confirmed, thanks for your response."

                print("confirm_competition: Replacing action message with: ", response_message)
                requests.post(event['response_url'], json=response_message)

                event['action_event'] = {
                    "destination": competition.channel,
                    "text": "Competition has been created by <@{}>. To register, try sending a message in this channel such as:\n '<@UCGV1M7GC> Register me'".format(user.slack_id)
                }
            else:
                # User is not the admin. Advise them.
                event['action_event'] = get_admin_error_message(user, competition)
        else:
            # No active competition found
            event['action_event'] = get_competition_not_found_message(user)
    return event

def cancel_competition(event, context):
    print("cancel_competition: Receieved event - ", event)

    with DatabaseManager("cancel_competition") as db:
        user = User.select().where((User.slack_id == event["user"]["id"])).first()
        competition = db.get_active_competition(event['actions'][0]["value"])
        
        if competition and competition.status == Competition.NEW:
            if user_is_admin_of_competition(user, competition):
                # User is admin and comp found, do actions
                competition.delete_instance()

                response_message = event['original_message']
                del response_message['attachments'][0]['actions']
                response_message['attachments'][0]['footer'] = "Your competition has been canceled, thanks for your response."
                print("response is now: ", response_message)

                requests.post(event['response_url'], json = response_message)

                event['action_event'] = {
                    "destination": user.slack_id,
                    "text": "Competition has been cancelled."
                }
            else:
                # User is not the admin. Advise them.
                event['action_event'] = get_admin_error_message(user, competition)
        else:
            # No active competition found
            event['action_event'] = get_competition_not_found_message(user)
    return event

def close_registration(event, context):
    print("close_registration: Receieved event - ", event)

    with DatabaseManager("cancel_competition") as db:
        user = User.select().where((User.slack_id == event["slack_profile"]["id"])).first()
        competition = db.get_active_competition(event['slack_event']['event']['channel'])

        if competition and competition.status == Competition.REGISTERING:
            if user_is_admin_of_competition(user, competition):
                # Comp exists in right state, set the status and send message
                participants = [x for x in competition.participants]
                text = "Are you sure you want to close registration? \n" + "Current participants are: \n"
                for participant in participants:
                    text += "<@{}>".format(participant.user.slack_id) + " \n"
                print("close_registration: list of participants is - ", participants)
                event['action_event'] = {
                    "destination": user.slack_id,
                    "text": text,
                    "attachments": [
                        {
                            "text": "Confirm or Cancel the close of registration",
                            "fallback": "Something went wrong, try closing registration again.",
                            "callback_id": "poolie_close_registration",
                            "color": "#3ab503",
                            "attachment_type": "default",
                            "actions": [
                                generate_button_attachment("Confirm", "confirm", "good", event['slack_event']['event']['channel']),
                                generate_button_attachment("Cancel", "cancel", "danger", event['slack_event']['event']['channel'])
                            ]
                        }
                    ]
                }            
            else:
                # User is not the admin. Advise them.
                event['action_event'] = get_admin_error_message(user, competition)
        else:
            # No active competition found
            event['action_event'] = get_competition_not_found_message(user)

    return event
