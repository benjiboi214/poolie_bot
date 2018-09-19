import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from playhouse.shortcuts import model_to_dict

from database.models import Competition, User
from database.util import DatabaseManager

from slack import generate_button_attachment

from misc import (get_admin_error_message, get_competition_not_found_message,
                   user_is_admin_of_competition)

def generate_draw(event, context):
    print("generate_draw: Receieved event - ", event)
    
    with DatabaseManager("cancel_competition") as db:
        user = User.select().where((User.slack_id == event["user"]["id"])).first()
        competition = db.get_active_competition(event['actions'][0]["value"])
        
        if competition and competition.status == Competition.GENERATE_DRAW:
            if user_is_admin_of_competition(user, competition):
                draw, created = db.get_or_create_draw(competition)
                if draw.times_around == None:
                    print("generate_draw: No draw times, sending message to collect")
                    event['action_event'] = {
                        "destination": user.slack_id,
                        "text": "How many times do you want to play eachother?",
                        "attachments": [
                            {
                                "text": "Select the number of times to play the roster.",
                                "fallback": "Something went wrong.",
                                "callback_id": "poolie_select_draw_times_round",
                                "color": "#3ab503",
                                "attachment_type": "default",
                                "actions": [
                                    generate_button_attachment("1", "1", "good", event['actions'][0]["value"]),
                                    generate_button_attachment("2", "2", "good", event['actions'][0]["value"]),
                                    generate_button_attachment("3", "3", "good", event['actions'][0]["value"]),
                                    generate_button_attachment("4", "4", "good", event['actions'][0]["value"])
                                ]
                            }
                        ]
                    }
                elif draw.finals == None:
                    print("generate_draw: No draw finals, sending message to collect")
                    event['action_event'] = {
                        "destination": user.slack_id,
                        "text": "Do you want to play finals at the end of the series?",
                        "attachments": [
                            {
                                "text": "Confirm whether you want to play finals. Alternatively, the top of the ladder will be declared the winner.",
                                "fallback": "Something went wrong.",
                                "callback_id": "poolie_select_draw_finals",
                                "color": "#3ab503",
                                "attachment_type": "default",
                                "actions": [
                                    generate_button_attachment("Confirm", "confirm", "good", event['actions'][0]["value"]),
                                    generate_button_attachment("Cancel", "cancel", "danger", event['actions'][0]["value"])
                                ]
                            }
                        ]
                    }
                else:
                    print("Wew, we have collected all the info we need!")
                    pass
            else:
                # User is not the admin. Advise them.
                event['action_event'] = get_admin_error_message(user, competition)
        else:
            # No active competition found
            event['action_event'] = get_competition_not_found_message(user)
    return event

def select_draw_times(event, context):
    print("select_draw_times: Receieved event - ", event)
    pass

def select_draw_finals(event, context):
    print("select_draw_finals: Receieved event - ", event)
    pass