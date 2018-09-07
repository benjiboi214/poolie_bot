import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from peewee import Model
from peewee import CharField, ForeignKeyField, DateTimeField, TimestampField
from db_util import db_connection
import datetime


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