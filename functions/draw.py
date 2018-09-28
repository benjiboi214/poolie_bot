import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

import requests
from playhouse.shortcuts import model_to_dict

from database.models import Competition, User, Draw, Round, Match, Participant
from database.util import DatabaseManager
from rounds import generate_round_lineup

from slack import generate_button_attachment

from misc import (get_admin_error_message, get_competition_not_found_message,
                   user_is_admin_of_competition)
from draw_data.matchups import draw_data

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

                    participants = [participant for participant in Participant.select().where((Participant.competition == competition.id))]
                    print("Times around: ", draw.times_around)
                    rounds = create_round_models(participants, competition, draw)
                    print("Created rounds: ", rounds)
                    text = "Draw Generated. Playing a {} round season, ".format(str(draw.times_around))
                    if draw.finals:
                        text += "with a finals series.\n"
                    else:
                        text += "without a finals series.\n"
                    text += "Round 1/{} Draw:\n".format(str(draw.times_around))
                    text += generate_round_lineup(rounds[1]['matches'])
                    event['action_event'] = {
                        "destination": competition.channel,
                        "text": text
                    }
            else:
                # User is not the admin. Advise them.
                event['action_event'] = get_admin_error_message(user, competition)
        else:
            # No active competition found
            event['action_event'] = get_competition_not_found_message(user)
    return event

def select_draw_times(event, context):
    print("select_draw_times: Receieved event - ", event)

    with DatabaseManager("select_draw_times") as db:
        user = User.select().where((User.slack_id == event["user"]["id"])).first()
        competition = db.get_active_competition(event['actions'][0]["value"])

        if competition and competition.status == Competition.GENERATE_DRAW:
            if user_is_admin_of_competition(user, competition):
                # Update the competition and trigger next action in flow
                draw = Draw.get(Draw.competition == competition)
                draw.times_around = int(event['sub_action'])
                draw.save()

                response_message = event['original_message']
                del response_message['attachments'][0]['actions']
                response_message['attachments'][0]['footer'] = "Roster will play {} time/s".format(event['sub_action'])

                print("select_draw_times: Replacing action message with: ", response_message)
                requests.post(event['response_url'], json=response_message)
            else:
                # User is not the admin. Advise them.
                event['action_event'] = get_admin_error_message(user, competition)
        else:
            # No active competition found
            event['action_event'] = get_competition_not_found_message(user)
    return event

def select_draw_finals(event, context):
    print("select_draw_finals: Receieved event - ", event)

    with DatabaseManager("select_draw_finals") as db:
        user = User.select().where((User.slack_id == event["user"]["id"])).first()
        competition = db.get_active_competition(event['actions'][0]["value"])

        if competition and competition.status == Competition.GENERATE_DRAW:
            if user_is_admin_of_competition(user, competition):
                # Update the competition and trigger next action in flow
                draw = Draw.get(Draw.competition == competition)
                if event['sub_action'] == 'confirm':
                  draw.finals = True
                  message = "Finals will be played at the end of the season."
                else:
                  draw.finals = False
                  message = "Finals will not be played at the end of the season."
                draw.save()

                response_message = event['original_message']
                del response_message['attachments'][0]['actions']
                response_message['attachments'][0]['footer'] = message

                print("select_draw_finals: Replacing action message with: ", response_message)
                requests.post(event['response_url'], json=response_message)
            else:
                # User is not the admin. Advise them.
                event['action_event'] = get_admin_error_message(user, competition)
        else:
            # No active competition found
            event['action_event'] = get_competition_not_found_message(user)
    return event

def create_round_models(players, competition, draw):
    # players is an array of participants
    # competition is the comp model
    # draw is the parent draw object
    times_around = draw.times_around
    with DatabaseManager("create_draw_models") as db:
        number_players = len(players)
        if number_players % 2 == 1:
            # odd number
            # create draw participant
            bye, created = db.get_or_create_participant(None, competition)
            players.append(bye)
            number_players += 1
        matchups = draw_data[number_players]

        players.insert(0, None)
        return_rounds = {}
        round_count = 1
        for time_around in range(times_around):
            time_around += 1
            if time_around % 2 == 1:
                # Normal Round
                for match_round in matchups['rounds']:
                    working_round = Round.create(draw=draw, number=round_count)
                    return_rounds[round_count] = {'round': working_round, 'matches': []}
                    for match in match_round:
                        match_model = Match.create(
                            draw_round=working_round,
                            home_participant=players[match['home']],
                            away_participant=players[match['away']])
                        return_rounds[round_count]['matches'].append(match_model)
                    round_count +=1
            else:
                for match_round in matchups['rounds']:
                    working_round = Round.create(draw=draw, number=round_count)
                    return_rounds[round_count] = {'round': working_round, 'matches': []}
                    for match in match_round:
                        match_model = Match.create(
                            draw_round=working_round,
                            home_participant=players[match['away']],
                            away_participant=players[match['home']])
                        return_rounds[round_count]['matches'].append(match_model)
                    round_count +=1
        return return_rounds

