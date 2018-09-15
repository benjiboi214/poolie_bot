import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from playhouse.shortcuts import model_to_dict

def user_is_admin_of_competition(user, competition):
    print("DEBUG user_is_admin_of_competition: Function Entry")
    if competition.admin.slack_id == user.slack_id and competition.admin.id == user.id:
        return True
    else:
        return False

def get_admin_error_message(user, competition):
    return {
        "destination": user.slack_id,
        "text": "You're not the admin of <#{}>. Ask <@{}> to complete the action!".format(competition.channel, competition.admin.slack_id)
    }

def get_competition_not_found_message(user):
    return {
        "destination": user.slack_id,
        "text": "Something went wrong, couldn't find the active competition."
    }