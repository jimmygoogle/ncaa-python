#from flask import jsonify
from project.ncaa import Ncaa
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

class Teams(Ncaa):
    def __init__(self):
        '''xxx'''

        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__year = str(datetime.datetime.now().year - 2)
        self.__api_key = 'dx2dgwhwscf4fwm64zpa69xd'

        self.__redis_client = redis.Redis(
            host=config.get('REDIS', 'REDIS_HOST'),
            port=config.get('REDIS', 'REDIS_PORT'),
            db=0,
            decode_responses=True
        )

        self.__db = MysqlPython()

    def get_tournament_id(self):
        # x = NCAAMB.NCAAMB('ep927w7b9ceadfnhxpadfyun')
        # self.debug(type(x))
        # response = x.get_tournament_list(100, 100)
        # self.debug(response)

        return 'cc2e6918-879a-4a91-a921-a071c71ef6a1'

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
        # stop here, we got a first four team placeholder in the main bracket
        if 'id' not in team:
            self.debug(team['source'])
            result = self.__db.query(
                proc = 'GetSportsRadarTeamData',
                params = [
                    team['source']['home_team']
                ]
            )

            self.debug(f"looking up {team['source']['home_team']}")
            self.debug(result)

            playin_home_team = result[0]['alias']

            result = self.__db.query(
                proc = 'GetSportsRadarTeamData',
                params = [
                    team['source']['away_team']
                ]
            )

            self.debug(f"looking up {team['source']['away_team']}")
            self.debug(result)

            playin_away_team = result[0]['alias']
            seed_id = result[0]['seedID']

            self.debug(f"Setting up playin {playin_home_team} / {playin_away_team} :: {game_id} :: {seed_id}")

            self.__db.insert(
                proc='InsertTeamsData',
                params=[
                    f"{playin_home_team} / {playin_away_team}",
                    seed_id,
                    game_id,
                    ' '
                ]
            )

            key = f"playin){team['source']['home_team']}_{team['source']['away_team']}"
            self.__redis_client.set(key, game_id)
            return

        self.debug(f"Setting up team {team['name']} ({team['id']}) for game {game_id}")

        result = self.__db.query(
            proc = 'GetSportsRadarTeamData',
            params = [team['id']]
        )

        self.debug(result)
        # use DB
        if result:
            self.debug(f"Found {team['name']} in DB")
            data = result[0]
            sportsradar_team_data_id = data['sportsradar_team_data_id']
        else:
            # we havent seen this team yet so go to sportsradar and get it
            self.debug(f"Getting {team['name']} from sportsradar")

            url = f"https://api.sportradar.us/ncaamb/trial/v7/en/teams/{team['id']}/profile.json?api_key={self.__api_key}"
            
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

        if skip_team_data != 1:
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
        #tournament_id = '86f1f414-88e9-4ad1-be69-740f4db52183'

        # url = f"https://api.sportradar.us/ncaamb/trial/v7/en/tournaments/{tournament_id}/schedule.json?api_key={self.__api_key}"
        # self.debug(url)
        # data = requests.get(url).json()

        #self.debug(data)
        #return
        # data = response
        # self.debug(f"teams type is {type(data)}")
        # self.debug(os.getcwd())
        f = open("/app/project/after-selection.json", "r")
        data = f.read()
        data = json.loads(data)

        # start setup by clearing old data
        if setup:
            self.__db.insert(proc='DeleteTeams', params=[])

            # intialize team / game relationship
            self.__db.insert(proc='InitializeTeamsGame', params=[])

        # * Top Left Quadrant: Regional Rank = 1 - South Regional in Example Provided
        # * Bottom Left Quadrant: Regional Rank = 4 - West Regional in Example Provided - add 8 to game
        # * Top Right Quadrant: Regional Rank = 2 - East Regional In Example Provided - add 16 to game
        # * Bottom Right Quadrant: Regional Rank = 3 - Midwest Regional in Example Provided - add 24 to game

        # used to set the game number of the quadrant based on the rank
        quadrant_game = {
            'First Four' : {
                1 : 0,
                4 : 0,
                2 : 0,
                3 : 0
            },
            'First Round' : {
                1 : 0,
                4 : 8,
                2 : 16,
                3 : 24
            },
            'Second Round' : {
                1 : 33,
                4 : 37,
                2 : 41,
                3 : 44
            },
            'Sweet 16' : {
                1 : 49,
                4 : 51,
                2 : 53,
                3 : 55
            },
            'Elite Eight' : {
                1 : 56,
                4 : 58,
                2 : 57,
                3 : 59
            },
            'Final Four' : {},
            'National Championship': {}
        }

        #score_data = {}
        score_data = defaultdict(dict)
        ff_idx = 1

        for round in data['rounds']:
            round_name = round['name']

            # # skip First Four ga
            # if setup == 0 and round_name == 'First Four':
            #     continue

            # skip other games as we are setting up only
            if setup == 1 and (round_name != 'First Round' and round_name != 'First Four'):
                continue
            
            for region in round['bracketed']:
                rank = region['bracket']['rank']

                for game in region['games']:
                    home_team = game['home']
                    away_team = game['away']

                    # get game from title
                    # ex: South Regional - First Round - Game 1
                    title_data = game['title'].rstrip().split(' ')
                    game_number  = int(title_data[-1])
                    game_number += quadrant_game[round_name][rank]

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
                           #game_number = 64 + ff_idx
                            # concat alias

                        self.setup_team(home_team, game_number, skip_team_data)
                        self.setup_team(away_team, game_number, skip_team_data)

                    # if setup == 1 and round_name == 'First Four':
                    #     ff_idx += 1
                    
                    continue

                    # figure out winner from completed game
                    if game['status'] == 'complete':
                        self.debug(f"trying to score {home_team} : {away_team}")
                        if 'home_points' in game:
                            home_team['score'] = game['home_points']

                            # TODO: if you wanted scores they could be found in this data
                            #score_data[game_number]['home_score'] = home_team['score']

                            if game['home_points'] > game['away_points']:
                                score_data[game_number] = self.__redis_client.get(home_team['id'])
                            else:
                                score_data[game_number] = self.__redis_client.get(away_team['id'])

                        # 
                        if round_name == 'First Four':
                            key = f"playin){home_team['id']}_{away_team['id']}"
                            game_id = self.__redis_client.get(key)
                            self.debug(f"updating bracket game {game_number} with winner of playin game {score_data[game_number]}")
                            del score_data[game_number]
        
        if setup:
            # add team / game relationship
            self.__db.insert(proc='InitializeTeamsGame', params=[])
 
        return score_data

    def get_scores(self):
        pass
