import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from playhouse.shortcuts import model_to_dict

from connection import DatabaseManagerBase
from models import Competition, Participant, User, Draw, Round, Match


def create_tables(event, context):
    print("create_tables: Receieved event - ", event)

    tables = [User, Competition, Participant, Draw, Round, Match]
    print("create_tables: Creating tables {}".format(tables))
    with DatabaseManagerBase() as db_connection:
        db_connection.connection.create_tables(tables)
    print("create_tables: Finished creating tables")
    return event

def drop_tables(event, context):
    print("drop_tables: Receieved event - ", event)

    tables = [User, Competition, Participant, Draw, Round, Match]
    print("drop_tables: Dropping tables {}".format(tables))
    with DatabaseManagerBase() as db_connection:
        db_connection.connection.drop_tables(tables)
    print("drop_tables: Finished Dropping tables")
    return {
        "statusCode": 200,
        "body": "Success"
    }


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
    
    def get_or_create_draw(self, competition):
        print("DEBUG get_or_create_draw: Function Entry")
        draw, created = Draw.get_or_create(
            competition=competition)
        if created:
            print("{context}: Draw created: {model}".format(context=self.context, model=model_to_dict(draw)))
        else:
            print("{context}: User retrieved: {model}".format(context=self.context, model=model_to_dict(draw)))
        return draw, created
