import os
import sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

def generate_round_lineup(matches):
    text = ""
    for match in matches:
        home_player = match.home_participant
        away_player = match.away_participant
        if home_player.user and away_player.user:
            text += "<@{home}> VS <@{away}> \n".format(
                home=home_player.user.slack_id,
                away=away_player.user.slack_id)
        elif not home_player.user:
            text += "BYE VS <@{away}> \n".format(
                away=away_player.user.slack_id)
        elif not away_player.user:
            text += "<@{home}> VS BYE \n".format(
                home=home_player.user.slack_id)
    return text

# def generate_player_actions(matches):
#     actions = []
#     home_player = match.home_participant
#     away_player = match.away_participant
#     for match in matches:
#         if home_player.user and away_player.user:
#            action.append(
#                {"destination": home_player + ',' + away_player,
#                "text": }
#            )
#         elif not home_player.user:

#         elif not away_player.user:

#     pass
#     # Given a round