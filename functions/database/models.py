import datetime
import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from peewee import (CharField, DateTimeField, ForeignKeyField, Model,
                    TimestampField, SmallIntegerField, BooleanField)

from connection import db_connection

class BaseModel(Model):
    created_date = DateTimeField(default=datetime.datetime.now)
    updated_date = TimestampField()
    class Meta:
        database = db_connection


class User(BaseModel):
    slack_id = CharField(unique=True)
    username = CharField()
    name = CharField()


class Competition(BaseModel):
    NEW = "N"  # Competition Created, not yet confirmed creation
    REGISTERING = "R"  # Competition Confirmed, accepting registrations, not yet closed.
    GENERATE_DRAW = "G"  # Registration Closed, generating draw, not yet started.
    PLAYING = "P"  # Competition Started, further status available on draw/round models
    FINISHED = "F"  # Games finished, winner found.
    STATUS_CHOICES = [
        (NEW, 'New'),
        (REGISTERING, 'Registering'),
        (GENERATE_DRAW, 'Generating Draw'),
        (PLAYING, "Playing"),
        (FINISHED, "Finished")
    ]
    channel = CharField(max_length=20)
    status = CharField(choices=STATUS_CHOICES, max_length=1)
    admin = ForeignKeyField(User, backref='admin_competitions')


class Participant(BaseModel):
    user = ForeignKeyField(User, backref='participants', null=True)
    competition = ForeignKeyField(Competition, backref='participants')

class Draw(BaseModel):
    competition = ForeignKeyField(Competition, backref='draw')
    times_around = SmallIntegerField(null=True)
    finals = BooleanField(null=True)
    
class Round(BaseModel):
    draw = ForeignKeyField(Draw, backref='rounds')
    number = SmallIntegerField()

class Match(BaseModel):
    draw_round = ForeignKeyField(Round, backref='matches')
    home_participant = ForeignKeyField(Participant, backref='home_matches')
    away_participant = ForeignKeyField(Participant, backref='away_matches')
    winner = ForeignKeyField(Participant, backref='wins', null=True)
    loser = ForeignKeyField(Participant, backref='losses', null=True)
