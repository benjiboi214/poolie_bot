import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from playhouse.shortcuts import model_to_dict

from connection import DatabaseManagerBase
from models import Competition, Participant, User


def create_tables(event, context):
    print("create_tables: Receieved event - ", event)

    tables = [User, Competition, Participant]
    print("create_tables: Creating tables {}".format(tables))
    with DatabaseManagerBase() as db_connection:
        db_connection.connection.create_tables(tables)
    print("create_tables: Finished creating tables")
    return event


class DatabaseManager(DatabaseManagerBase):
    def __init__(self, context):
        super(DatabaseManager, self).__init__()
        self.context = context
    
    def get_or_create_user(self, slack_id, name, real_name):
        print("DEBUG get_or_create_user: Function Entry")
        user, created = User.get_or_create(
            slack_id=slack_id,
            username=name,
            name=real_name)
        if created:
            print("{context}: User created: {model}".format(context=self.context, model=model_to_dict(user)))
        else:
            print("{context}: User retrieved: {model}".format(context=self.context, model=model_to_dict(user)))
        return user, created
    
    def get_or_create_participant(self, user, competition):
        print("DEBUG get_or_create_participant: Function Entry")
        participant, created = Participant.get_or_create(
            user=user,
            competition=competition
        )
        if created:
            print("{context}: Participant created: {model}".format(context=self.context, model=model_to_dict(participant)))
        else:
            print("{context}: Participant retrieved: {model}".format(context=self.context, model=model_to_dict(participant)))
        return participant, created

    def get_active_competition(self, channel):
        print("DEBUG get_active_competition: Function Entry")
        competition = Competition.select().where(
            (Competition.channel == channel) &
            (Competition.status != Competition.FINISHED)
        ).first()
        if competition is None:
            print("{context}: No active Competition in {channel}".format(context=self.context, channel=channel))
        else:
            print("{context}: Active Competition found in {channel}: {model}".format(context=self.context, channel=channel, model=model_to_dict(competition)))
        return competition

    def get_or_create_active_competition(self, channel, admin):
        print("DEBUG get_or_create_active_competition: Function Entry")
        created = False
        # Select competition in channel where comp is not finished
        competition = self.get_active_competition(channel)
        if competition is not None:
            print("{context}: Competition already running in {channel}: {model}".format(context=self.context, channel=channel, model=model_to_dict(competition)))
        else:
            competition = Competition.create(
                channel=channel,
                status=Competition.NEW,
                admin=admin)
            created = True
            print("{context}: Competition created {model}".format(context=self.context, model=model_to_dict(competition)))
        return competition, created

