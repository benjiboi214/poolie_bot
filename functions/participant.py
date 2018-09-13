import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from playhouse.shortcuts import model_to_dict

from database.models import Competition, Participant, User
from database.util import DatabaseManager

def register_participant(event, context):
    print("register_participant: Receieved event - ", event)

    with DatabaseManager("register_participant") as db:
        # Get or create user
        user, user_created = db.get_or_create_user(
            event['slack_profile']['id'],
            event['slack_profile']['name'],
            event['slack_profile']['real_name'])
        competition = db.get_active_competition(event['slack_event']['event']['channel'])

        message = { "destination": user.slack_id }

        if competition and competition.status == Competition.REGISTERING:
            print("register_participant: Competition is registering.")
            participant, participant_created = db.get_or_create_participant(user, competition)
            if participant_created:
                print("register_participant: Participant created")
                message["text"] = "Thanks for resgistering for this competition! Pester <@{}> to get it started.".format(competition.admin.slack_id)
            else:
                print("register_participant: Participant already exists, sending warning text")
                message["text"] = "It looks like you're already registered for this competition. Pester the admin to get it started."
        elif competition and competition.status == Competition.NEW:
            print("register_participant: Competition is new.")
            message["text"] = "Sorry, you've tried registering for a competition that is not yet open for registration."
        elif competition and (competition.status == Competition.GENERATE_DRAW or competition.status == Competition.PLAYING):
            print("register_participant: Competition is closed.")
            message["text"] = "Sorry, you've tried registering for a competition that has already closed. Please wait for the next competition to register."
        else:
            print("register_participant: Competition does not exist")
            message["text"] = "Sorry, there are no competitions running in this channel."

    event['action_event'] = message
    return event
