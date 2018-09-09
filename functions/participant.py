import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from db_util import DatabaseManager
from models import Competition, User, Participant
from playhouse.shortcuts import model_to_dict


def register_participant(event, context):
    print("register_participant: Receieved event - ", event)

    with DatabaseManager():
        # Get or create user
        user, created = User.get_or_create(
            slack_id=event['slack_profile']['id'],
            username=event['slack_profile']['name'],
            name=event['slack_profile']['real_name']
        )
        print("register_participant: User found - ", model_to_dict(user))
  
        # Get not done competition
        competition = Competition.select().where(
            (Competition.channel == event['slack_event']['event']['channel']) &
            (Competition.status != Competition.FINISHED)
        ).first()
        if competition:
            print("register_participant: Competition found - ", model_to_dict(competition))

        message = { "destination": user.slack_id }
        # If not registering, message that registration not currently open
        if not competition:
            print("register_participant: Competition does not exist")
            message["text"] = "Sorry, there are no competitions running in this channel."
        elif competition.status == Competition.NEW:
            print("register_participant: Competition is new.")
            message["text"] = "Sorry, you've tried registering for a competition that is not yet open for registration."
        elif competition.status == Competition.GENERATE_DRAW or competition.status == Competition.PLAYING:
            print("register_participant: Competition is closed.")
            message["text"] = "Sorry, you've tried registering for a competition that has already closed. Please wait for the next competition to register."
        else:
            print("register_participant: Competition is registering.")
            # Get participant for given user and comp
            participant, created = Participant.get_or_create(
                user=user,
                competition=competition
            )
            print("register_participant: Participant found - ", model_to_dict(participant))

            if created:
                # if not present, create, send message to user confirming registration.
                print("register_participant: Participant created")
                message["text"] = "Thanks for resgistering for this competition! Pester <@{}> to get it started.".format(competition.admin.slack_id)
            else:
                # if already present, message that already registered
                print("register_participant: Participant already exists, sending warning text")
                message["text"] = "It looks like you're already registered for this competition. Pester the admin to get it started."
                

    event['action_event'] = message
    return event