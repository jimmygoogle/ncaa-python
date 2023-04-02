#from flask import jsonify
from project.ncaa import Ncaa
from collections import OrderedDict
from project.mysql_python import MysqlPython
import requests 
import configparser
import datetime
import re
import time
import json
import os
import time

class Teams(Ncaa):
    def __init__(self):
        
        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__year = str(datetime.datetime.now().year - 1)
        self.__api_key = 'ep927w7b9ceadfnhxpadfyun'

        self.__db = MysqlPython()

    def get_tournament_id(self):
        # x = NCAAMB.NCAAMB('ep927w7b9ceadfnhxpadfyun')
        # self.debug(type(x))
        # response = x.get_tournament_list(100, 100)
        # self.debug(response)
        url = f"https://api.sportradar.us/ncaamb/trial/v7/en/tournaments/{self.__year}/PST/schedule.json?api_key={self.__api_key}"
        self.debug(url)
        response = requests.get(url).json()
        self.debug(f"id type is {type(response)}")

        for tournament in response['tournaments']:
            if tournament['name'] == "NCAA Men's Division I Basketball Tournament":
                tournament_id = tournament['id']
                continue

        self.debug(f"tournament_id is {tournament_id}")
        return tournament_id

    def setup_team(self, team, game_id, skip_team_data):
        self.debug(f"Setting up team {team['name']} ({team['id']})")

        url = f"https://api.sportradar.us/ncaamb/trial/v7/en/teams/{team['id']}/profile.json?api_key={self.__api_key}"
        
        data = None
        response = requests.get(url)

        if response.ok:
            data = response.json()
        else:
            if response.reason == 'Forbidden':
                time.sleep(5)
                self.debug(f"sleeping bc of 403 with {team['name']} ({team['id']})")
                self.setup_team(team, game_id)

        self.debug(f"setup_team done: {team['name']} ({team['id']})")
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

        if skip_team_data != 1:
            self.__db.insert(
                proc='InsertTeamsData',
                params=[
                    data['market'],
                    team['seed'],
                    game_id,
                    sportsradar_team_data_id
                ]
            )

        time.sleep(1)

    def setup_teams(self):
        # tournament_id = self.get_tournament_id()

        # url = f"https://api.sportradar.us/ncaamb/trial/v7/en/tournaments/{tournament_id}/schedule.json?api_key={self.__api_key}"
        # self.debug(url)
        # response = requests.get(url).json()
        # data = response
        # self.debug(f"teams type is {type(data)}")
        self.debug(os.getcwd())
        f = open("/app/project/data.json", "r")
        data = f.read()

        data = json.loads(data)
        self.debug(type(data))

        setup = 1

        # 
        if setup:
            self.__db.insert(proc='DeleteTeams', params=[])

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

        jim = {}

        for round in data['rounds']:
            # # skip the first four games
            # if round['name'] == 'First Four':
            #     continue

            sequence = round['sequence']
            round_name = round['name']

            # if round_name != 'First Round':
            #     continue

            for region in round['bracketed']:
                rank = region['bracket']['rank']

                for game in region['games']:
                    home_team = game['home']
                    away_team = game['away']
                    self.debug(home_team)
                    self.debug(away_team)
                    # self.debug(game['title'])

                    # get game from title
                    # ex: South Regional - First Round - Game 1
                    title_data = game['title'].rstrip().split(' ')
                    self.debug(title_data)
                    game_number  = int(title_data[-1])
                    self.debug(f"game_number is {game_number}")
                    self.debug(quadrant_game)
                    self.debug(quadrant_game[round_name])
                    game_number += quadrant_game[round_name][rank]
                    self.debug(f"real game_number is {game_number}")

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

                        self.setup_team(home_team, game_number, skip_team_data)
                        self.setup_team(away_team, game_number, skip_team_data)
                        continue

                    # figure out winner from completed game
                    if game['status'] == 'closed':
                        if game['home_points'] > game['away_points']:
                            home_team['winner'] = 1
                        else:
                            away_team['winner'] = 1

                    if re.search('win', home_team['name']):
                        home_team['name'] = 'none'

                    if re.search('win', away_team['name']):
                        away_team['name'] = 'none'

                    print(f"game {game_number}: {away_team['name']} at {home_team['name']}")

                    jim[ game_number] = {
                        'home_team': home_team['name'],
                        'away_team': away_team['name']
                    }
        
        if setup:

            # add team / game relationship
            self.__db.insert(proc='InitializeTeamsGame', params=[])

        return jim

    def get_scores(self):
        pass
