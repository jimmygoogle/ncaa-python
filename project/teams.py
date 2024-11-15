#from flask import jsonify
from project.sportsradar import SportRadar
from collections import defaultdict, OrderedDict
from project.mysql_python import MysqlPython
import requests 
import configparser
import datetime
import re
import time
import json
import os
import time
import redis

class Teams(SportRadar):
    def __init__(self):
        SportRadar.__init__(self)

        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__redis_client = redis.Redis(
            host=config.get('REDIS', 'REDIS_HOST'),
            port=config.get('REDIS', 'REDIS_PORT'),
            db=0,
            decode_responses=True
        )

        self.__db = MysqlPython()

    def get_tournament_id(self):
        # hard code for now (2024)
        return '3f50b4cf-b319-4df2-90c0-8fc549742710'

        tournament_id = self.__redis_client.get('tournament_id')

        if tournament_id:
            self.debug(f"tournament_id is set {tournament_id}")
            return tournament_id
        
        url = f"https://api.sportradar.us/ncaamb/trial/v7/en/tournaments/{self.__year}/PST/schedule.json?api_key={self.__api_key}"
        self.debug(url)
        response = requests.get(url).json()
        self.debug(f"id type is {type(response)}")

        for tournament in response['tournaments']:
            if tournament['name'] == "NCAA Men's Division I Basketball Tournament":
                tournament_id = tournament['id']
                continue

        self.debug(f"tournament_id is {tournament_id}")
        self.__redis_client.set('tournament_id', tournament_id)
        return tournament_id

    def setup_team(self, team, game_id, skip_team_data):
        # we got a first four team placeholder in the main bracket so put in placeholder game
        if 'id' not in team:
            result = self.__db.query(
                proc = 'GetSportsRadarTeamData',
                params = [
                    team['source']['home_team']
                ]
            )

            playin_home_team = result[0]['alias']

            result = self.__db.query(
                proc = 'GetSportsRadarTeamData',
                params = [
                    team['source']['away_team']
                ]
            )

            playin_away_team = result[0]['alias']
            seed_id = result[0]['seedID']

            # self.debug(f"Setting up playin {playin_home_team} / {playin_away_team} :: {game_id} :: {seed_id}")

            playin_team_id = self.__db.insert(
                proc='InsertTeamsData',
                params=[
                    f"{playin_home_team} / {playin_away_team}",
                    seed_id,
                    game_id,
                    ' '
                ]
            )

            key = f"playin_{team['source']['home_team']}_{team['source']['away_team']}"
            self.__redis_client.set(key, playin_team_id)
            return

        # self.debug(f"Setting up team {team['name']} ({team['id']}) for game {game_id}")

        result = self.__db.query(
            proc = 'GetSportsRadarTeamData',
            params = [team['id']]
        )

        # use DB
        if result:
            self.debug(f"Found {team['name']} in DB")
            data = result[0]
            sportsradar_team_data_id = data['sportsradar_pk']
            data['id'] = team['id']
        else:
            # we havent seen this team yet so go to sportsradar and get it
            self.debug(f"Getting {team['name']} from sportsradar")
            url = f"{self.sportsradar_url}/teams/{team['id']}/profile.json?api_key={self.api_key}"
            
            data = None
            response = requests.get(url)

            if response.ok:
                data = response.json()
            else:
                if response.reason == 'Forbidden':
                    time.sleep(2)
                    self.debug(f"sleeping bc of 403 with {team['name']} ({team['id']})")
                    self.setup_team(team, game_id, skip_team_data)
                    return

            self.debug(f"setup_team done: {team['name']} ({team['id']}) {skip_team_data}")
            #self.debug(data)

            # add data to DB
            sportsradar_team_data_id = self.__db.insert(
                proc='InsertSportsRadarTeamData',
                params=[
                    data['id'],
                    data['name'],
                    data['market'],
                    data['alias']
                ]
            )

            self.debug(f"sportsradar_team_data_id is {sportsradar_team_data_id} :: {skip_team_data}")

        #if skip_team_data != 1:
        team_id = self.__db.insert(
            proc='InsertTeamsData',
            params=[
                data['market'],
                team['seed'],
                game_id,
                sportsradar_team_data_id
            ]
        )

        self.__redis_client.set(data['id'], team_id)

    def get_team_data(self, setup = 1):
        '''Get team / game data from SportsRadar'''

        tournament_id = self.get_tournament_id()

        # url = f"{self.sportsradar_url}/tournaments/{tournament_id}/schedule.json?api_key={self.api_key}"
        # data = requests.get(url).json()
        # self.debug(data)

        # load from file
        f = open("/app/project/data/after-selection.json", "r")
        #f = open("/app/project/data/after-first-four-playin-game-1.json", "r")
        #f = open("/app/project/data/after-few-games-round-1.json", "r")
        #f = open("/app/project/data/day-1-complete.json", "r")
        #f = open("/app/project/data/after-day-2.json", "r")
        #f = open("/app/project/data/sweet-16.json", "r")
        #f = open("/app/project/data/elite-8.json", "r")
        #f = open("/app/project/data/final-4-half-set.json", "r")
        #f = open("/app/project/data/final-4.json", "r")
        #f = open("/app/project/data/championship-data.json", "r")
        
        data = f.read()
        data = json.loads(data)

        # start setup by clearing old data
        if setup:
            self.__db.insert(proc='DeleteTeams', params=[])
            self.__redis_client.delete('base_team_data')
            self.__redis_client.delete('xx')

        # * Top Left Quadrant: Regional Rank     = 1  - South Regional in Example Provided
        # * Bottom Left Quadrant: Regional Rank  = 4  - West Regional in Example Provided   - add 8 to game
        # * Top Right Quadrant: Regional Rank    = 2  - East Regional In Example Provided   - add 16 to game
        # * Bottom Right Quadrant: Regional Rank = 3 - Midwest Regional in Example Provided - add 24 to game

        # used to set the game number of the quadrant based on the rank
        quadrant_game = {
            'First Four' : {
                1 : 0,
                4 : 0,
                2 : 0,
                3 : 0
            },
            # 32 games - 8 per region
            'First Round' : {
                1 : 0,
                4 : 8,
                2 : 16,
                3 : 24
            },
            # 16 games - 4 per region
            'Second Round' : {
                1 : 32,
                4 : 36,
                2 : 40,
                3 : 44
            },
            # 8 games - 2 per region
            'Sweet 16' : {
                1 : 48,
                4 : 50,
                2 : 52,
                3 : 54
            },
            # 4 games - 1 per region
            'Elite Eight' : {
                1 : 56,
                4 : 57,
                2 : 58,
                3 : 59
            },
            # 2 games
            'Final Four' : {
                1 : 60,
            },
            # 1 game
            'National Championship': {
                1 : 62
            }
        }

        score_data = defaultdict(dict)
        upset_data = defaultdict(dict)

        score_data_key = 'xx'
        stored_score_data = self.__redis_client.get(score_data_key)

        if stored_score_data is None:
            stored_score_data = {}
        else:
            stored_score_data = json.loads(stored_score_data)

        for round in data['rounds']:
            round_name = round['name']
            # self.debug(f"======= {round_name} ======== ")

            # skip other games as we are setting up only
            if setup == 1 and (round_name != 'First Round' and round_name != 'First Four'):
                continue
            
            # the final four and national championship data
            # is not 'bracketed' so we will make the data look the same
            if not round['bracketed']:
                round['bracketed'] = [
                    {
                        'bracket': { 'rank': 1 },
                        'games': round['games']
                    }
                ]

            for region in round['bracketed']:
                rank = region['bracket']['rank']

                if rank is None:
                    rank = 1

                for game in region['games']:
                    home_team = game['home']
                    away_team = game['away']

                    # get game from title
                    # ex: South Regional - First Round - Game 1
                    title_data = game['title'].rstrip().split(' ')

                    # get game number from title
                    try:
                        game_number = int(title_data[-1])
                    except ValueError:
                        game_number = 1

                    # self.debug(f"title is {game['title']} :: game is {game_number} :: rank is {rank}")
                    game_number += quadrant_game[round_name][rank]

                    store_tiebreaker_points = 0
                    tie_breaker_points = 0
                    if round_name == 'National Championship':
                        store_tiebreaker_points = 1

                    if round_name == 'First Four':
                        game_number += 64

                    scored_game_number_key = f"game_scored_{game_number}"

                    # "home": {
                    #     "name": "Arizona Wildcats",
                    #     "alias": "ARIZ",
                    #     "id": "9b166a3f-e64b-4825-bb6b-92c6f0418263",
                    #     "seed": 2
                    # },

                    # setup teams / add to DB, etc
                    if setup == 1 and (round_name == 'First Round' or round_name == 'First Four'):
                        skip_team_data = 0
                        if round_name == 'First Four':
                            skip_team_data = 1
                            game_number += 64

                        self.setup_team(home_team, game_number, skip_team_data)
                        self.setup_team(away_team, game_number, skip_team_data)

                    games_already_scored = None
                    #if not setup:
                    #    games_already_scored = self.__redis_client.get(scored_game_number_key)

                    # if the game was already scored then stop
                    if games_already_scored:
                        continue

                    # figure out winner from completed games
                    if not setup and (game['status'] == 'complete' or game['status'] == 'closed'):
                        self.debug(f"trying to score ({game_number}) {home_team['name']} vs {away_team['name']}")

                        if 'home_points' in game:
                            upset_data[game_number] = 0

                            home_team_id = int(self.__redis_client.get(home_team['id']))
                            away_team_id = int(self.__redis_client.get(away_team['id']))

                            self.debug(f"home_team_id is {home_team_id} for {game_number}")
                            self.debug(f"away_team_id is {away_team_id} for {game_number}")

                            #if 1==1:
                            #if round_name != 'First Four':
                            stored_score_data[game_number] = defaultdict(dict)
                            stored_score_data[game_number][home_team_id] = defaultdict(dict)
                            stored_score_data[game_number][away_team_id] = defaultdict(dict)

                            # add scores
                            stored_score_data[game_number][home_team_id]['score'] = game['home_points']
                            stored_score_data[game_number][away_team_id]['score'] = game['away_points']

                                # procedure = 'AddTeamsGameScore'

                                # self.__db.update(
                                #     proc = procedure,
                                #     params = [
                                #         game_number,
                                #         home_team_id,
                                #         game['home_points']
                                #     ]
                                # )

                                # self.__db.update(
                                #     proc = procedure,
                                #     params = [
                                #         game_number,
                                #         away_team_id,
                                #         game['away_points']
                                #     ]
                                # )

                            #
                            if store_tiebreaker_points:
                                tie_breaker_points = game['home_points'] + game['away_points']

                            if game['home_points'] > game['away_points']:
                                self.debug(f"{home_team['name']} won")
                                score_data[game_number] = home_team_id
                                team_guid = home_team['id']

                                # add styling for game outcomes
                                stored_score_data[game_number][home_team_id]['css'] = 'game-winner'
                                stored_score_data[game_number][away_team_id]['css'] = 'game-loser'

                                if home_team['seed'] > away_team['seed']:
                                    upset_data[game_number] = 1
                                    # self.debug("====upset====")

                            else:
                                self.debug(f"{away_team['name']} won")
                                score_data[game_number] = away_team_id
                                team_guid = away_team['id']

                                # add styling for game outcomes
                                stored_score_data[game_number][home_team_id]['css'] = 'game-loser'
                                stored_score_data[game_number][away_team_id]['css'] = 'game-winner'

                                if away_team['seed'] > home_team['seed']:
                                    # self.debug("====upset====")
                                    upset_data[game_number] = 1

                        # switch the name of the playin game matchup to the winner of the playin game
                        if round_name == 'First Four':
                            key = f"playin_{home_team['id']}_{away_team['id']}"
                            playin_team_id = self.__redis_client.get(key)

                            self.debug(f"updating playin team {playin_team_id} with {team_guid}")
                            self.__db.update(
                                proc='UpdateTeam',
                                params=[
                                    playin_team_id,
                                    team_guid
                                ]
                            )

                            self.__redis_client.set(team_guid, playin_team_id)

                            # self.debug(f"updating playin game team name with {team_guid}")
                            del score_data[game_number]

                        # set game to scored so we dont reprocess each time
                        #self.__redis_client.set(scored_game_number_key, 1)
 
        # store score data
        self.__redis_client.set(score_data_key, json.dumps(stored_score_data))

        if setup:
            # intialize team / game relationship
            self.__db.insert(proc='InitializeTeamsGame', params=[])
            self.__db.insert(proc='InitializeTeamsGameScore', params=[])

        return {
            "score_data": score_data,
            "upset_data": upset_data,
            "tie_breaker_points": tie_breaker_points
        }
