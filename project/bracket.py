from flask import request, jsonify, current_app
from project.ncaa import Ncaa
from project.user import User
from project.pool import Pool
from project.teams import Teams
from project.confirmation_email import send_confirmation_email
from project.mysql_python import MysqlPython
from collections import defaultdict
import ast
import configparser
import redis
import json
import requests
import datetime
import time
from collections import defaultdict

class Bracket(Ncaa):
    '''Bracket class to get/set bracket information for a user'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        self.__pool = Pool()
        self.__user = User()

        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__redis_client = redis.Redis(
            host=config.get('REDIS', 'REDIS_HOST'),
            port=config.get('REDIS', 'REDIS_PORT'),
            db=0,
            decode_responses=True
        )

    def get_base_teams(self, include_scores = 1):
        '''Get base teams data for display'''
        
        key = f"base_team_data{include_scores}"
        base_team_data = self.__redis_client.get(key)

        # load base team data from cache if we can
        if base_team_data is not None:
            return json.loads(base_team_data)

        score_data_key = 'xx'
        stored_score_data = self.__redis_client.get(score_data_key)

        if stored_score_data is None:
            stored_score_data = {}
        else:
            stored_score_data = json.loads(stored_score_data)

        # get base teams from DB
        team_data = self.__db.query(proc = 'GetBaseTeams', params = [])

        if len(stored_score_data) > 0:
            for team in team_data:
                game_id = str(team['gameID'])
                team_id = str(team['teamID'])

                # add in scores and styling
                if game_id in stored_score_data:
                    team['pickCSS'] = stored_score_data[game_id][team_id]['css']

                    if include_scores == 1:
                        team['score'] = stored_score_data[game_id][team_id]['score']
                    

        # store team data in redis
        self.__redis_client.set(key, json.dumps(team_data))

        return team_data

    def get_empty_picks(self):
        '''
        Set empty user picks data for an empty bracket
        TODO: Fix this as it is really hacky
        '''
        
        empty_data = []
        for index in range(63):
            data = {
                'teamID': '',
                'seedID': '',
                'teamName': '',
                'pickCSS': '',
            }

            empty_data.append(data)
        
        return empty_data
    
    def get_master_bracket_data(self):
        '''Get master bracket data for display'''

        return self.get_user_bracket_for_display(
            is_admin = 1,
            user_token = None,
            action = 'view',
            bracket_type = 'normalBracket'
        )

    def get_user_picks(self, **kwargs):
        '''Get the picks for the user (token)'''

        user_token = kwargs['user_token']
        is_admin = kwargs['is_admin']

        # figure out which procedure to call to get the picks
        proc = 'UserDisplayBracket'
        params = [user_token]

        if is_admin:
            proc = 'MasterBracket'
            params = []
            
            admin_picks = []

            # handle missing picks from the the master bracket
            for index in range (64):
                admin_picks.append({
                    'pickCSS': '', 
                    'seedID': '',
                    'teamName': '',
                    'teamID' : 0, 
                    'gameID': 0,
                    'upset': 0,
                    'logo_name': '',
                    'score': '',
                })

        # get the picks from the DB
        user_picks = self.__db.query(proc = proc, params = params)
        self.debug(json.dumps(user_picks, indent=4))

        # get cached score data
        score_data_key = 'xx'
        stored_score_data = self.__redis_client.get(score_data_key)

        if stored_score_data is None:
            stored_score_data = {}
        else:
            stored_score_data = json.loads(stored_score_data)
    
        self.debug(json.dumps(stored_score_data, indent=4))

        # handle missing picks from the the master bracket by using the empty bracket and filling in the missing picks
        if is_admin:
            for pick in user_picks:
                admin_picks[ pick['gameIDCalc'] ] = {
                    'gameID': pick['gameID'],
                    'teamID': pick['teamID'],
                    'seedID': pick['seedID'],
                    'teamName': pick['teamName'],
                    'logo_name': pick['logo_name'],
                    'upset': pick['upset'],
                    'alias': pick['alias'],
                    'pickCSS': '',
                    'score': '',
                }

                user_picked_game_id = str(self.set_next_game(pick['gameID']))
                team_id = str(pick['teamID'])

                # add scores and styling
                if user_picked_game_id in stored_score_data:
                    admin_picks[ pick['gameIDCalc'] ]['pickCSS'] = stored_score_data[user_picked_game_id][team_id]['css']
                    admin_picks[ pick['gameIDCalc'] ]['score'] = stored_score_data[user_picked_game_id][team_id]['score']

            user_picks = admin_picks
        else:
            for pick in user_picks:
                user_picked_game_id = str(pick['gameID'])
                #user_picked_game_id = str(self.set_next_game(pick['gameID']))
                team_id = str(pick['teamID'])
                self.debug(f"user_picked_game_id is {user_picked_game_id}")
                self.debug(f"team_id is {team_id}")
                # add scores and styling
                if user_picked_game_id in stored_score_data:
                    self.debug(stored_score_data[user_picked_game_id])
                    if team_id in stored_score_data[user_picked_game_id]:
                        pick['pickCSS'] = stored_score_data[user_picked_game_id][team_id]['css']
                        #pick['score'] = stored_score_data[user_picked_game_id][team_id]['score'] 
                    else:
                        pick['score'] = ''
                        pick['pickCSS'] = 'game-loser'
        return user_picks   
    
    def get_user_bracket_for_display(self, **kwargs):
        '''Get user picks and information so we can display their bracket'''

        action = kwargs['action']
        is_admin = kwargs['is_admin']
        user_token = kwargs['user_token']
        bracket_type = kwargs['bracket_type']

        pool_name = ''
        if is_admin:
            # try and pull bracket from cache as the master bracket will be most viewed
            user_picks = self.__redis_client.get('master_bracket_picks')

            # we have cached data so use it
            if user_picks is not None:
                return {
                    'team_data': self.get_base_teams(), 
                    'user_picks': json.loads(user_picks), 
                    'user_info': {}, 
                    'bracket_display_name': '',
                    'upset_bonus_data': {},
                }

            pool_name = self.__pool.get_admin_pool_name()
        else: 
            pool_name = self.__pool.get_pool_name()
            if pool_name is None:
                result = self.__db.query(proc = 'GetPoolFromUser', params = [user_token])
                pool_name = result[0]['pool_name']
                self.__pool.set_pool_name(pool_name)

        # get the user picks
        user_picks = self.get_user_picks(is_admin = is_admin, user_token = user_token)
        #self.debug(user_picks)

        # TODO: remove?
        # # if this is a sweet 16 bracket fill in the 2 previous rounds from master 
        # if bracket_type == 'sweetSixteenBracket':    
        #     master_bracket_picks = self.__db.query(proc = 'MasterBracket', params = [])
        #     user_picks = master_bracket_picks + user_picks

        # set styling for incorrect picks and add upset bonus data
        #incorrect_picks = {}
        upset_bonus_data = {}

        # loop though picks
        # for pick in user_picks:
        #     upset_bonus_data[ pick['gameID'] ] = int(pick['upset'])

        # get the base teams (top 64)
        team_data = self.get_base_teams(include_scores=0)

        # if we have a real user then get some additional info
        if user_token is not None:
            proc = 'GetUserByDisplayToken'
            
            if action == 'edit':
                proc = 'GetUserByEditToken'

            user_info = self.__db.query(proc = proc, params = [user_token, pool_name])
            self.__user.set_username(user_info[0]['userName'])
            
            # set bracket display name
            bracket_display_name = self.__user.set_user_bracket_name()
        else:
            user_info = {}
            bracket_display_name = ''
    
        # cache the master bracket picks
        if is_admin == 1:
            self.__redis_client.set('master_bracket_picks', json.dumps(user_picks))

        return {
            'team_data': team_data, 
            'user_picks': user_picks, 
            'user_info': user_info, 
            'bracket_display_name': bracket_display_name,
            'upset_bonus_data': upset_bonus_data,
        }

    def process_user_bracket(self, **kwargs):
        '''Process the data the user submitted and add it to the DB'''

        if not kwargs['is_admin'] and not self.__pool.are_pools_open():
            error = 'The pool is no longer open.'
            message = ''

        else:
            # process all of the user's picks and put them into the DB
            self.process_pick_data(**kwargs)
            
            # TODO handle errors from processing
            error = ''

            # send confirmation email if this is a new bracket
            pool_name = self.__pool.get_pool_name()

            if kwargs['action'] == 'add' and pool_name != 'test':
                # # TODO: fix this
                # # url = request.url_root
                url = 'https://www.itsawesomebaby.com/'
                token = self.__user.get_edit_token()
                bracket_type_label = request.values['bracket_type_label']

                results = send_confirmation_email.s(
                    token = token,
                    url = url,
                    pool_name = pool_name,
                    pool_status = self.__pool.check_pool_status(),
                    email_address = request.values['email_address'],
                    bracket_type_name = request.values['bracket_type_name'],
                    bracket_type_label = bracket_type_label,
                    username = request.values['username']
                ).apply_async(seconds=10)
                edit_url = f"{url}bracket/{bracket_type_label}/{token}?action=e"
                message = f"Your bracket has been submitted.<br/>Good luck!<br/><br/>You can edit your bracket <a href='{edit_url}'>here</a> until the tip off of the first game on Thursday."
            
            # set updated message
            else:
                message = 'Your bracket has been updated.'
                
                # score all brackets if we have just updated the admin bracket
                if kwargs['is_admin']:
                    self.score_all_brackets()

        return jsonify({
            'message' : message,
            'error': error
        })

    def set_next_game(self, game_id):
        '''Set the next game the user will play in in the next round'''

        game_mappings = {
            0: 0,
            1: 33,
            2: 33,
            3: 34,
            4: 34,
            5: 35,
            6: 35,
            7: 36,
            8: 36,
            9: 37,
            10: 37,
            11: 38,
            12: 38,
            13: 39,
            14: 39,
            15: 40,
            16: 40,
            17: 41,
            18: 41,
            19: 42,
            20: 42,
            21: 43,
            22: 43,
            23: 44,
            24: 44,
            25: 45,
            26: 45,
            27: 46,
            28: 46,
            29: 47,
            30: 47,
            31: 48,
            32: 48,
            33: 49,
            34: 49,
            35: 50,
            36: 50,
            37: 51,
            38: 51,
            39: 52,
            40: 52,
            41: 53,
            42: 53,
            43: 54,
            44: 54,
            45: 55,
            46: 55,
            47: 56,
            48: 56,
            49: 57,
            50: 57,
            51: 58,
            52: 58,
            53: 59,
            54: 59,
            55: 60,
            56: 60,
            57: 61,
            58: 61,
            59: 62,
            60: 62,
            61: 63,
            62: 63,
            63: None,
        }

        return game_mappings[game_id]

    def process_pick_data(self, **kwargs):
        '''Process the user picks and add them to the DB'''

        # figure out if we are editing the master bracket since we call different procedures
        is_admin = 0
        if 'is_admin' in kwargs and kwargs['is_admin'] is not None and kwargs['is_admin'] != 0 :
            is_admin = 1
            
            # update tie breaker points
            self.debug(f"UpdateTieBreakerPoints {kwargs['tie_breaker_points']}")
            self.__db.update(proc = 'UpdateTieBreakerPoints', params = [
                kwargs['tie_breaker_points']
            ])

        # we have an edit token set it so the user can be updated
        if 'edit_user_token' in kwargs:
            self.__user.set_edit_token(kwargs['edit_user_token'])

        # add/edit user data:
        user_id = self.__user.update_user_data()
        
        # clear out the user's picks and set insert procedure
        clear_proc = 'ResetBracket'
        insert_proc = 'InsertBracketData'
        params = [user_id]

        # clear out master picks
        if is_admin == 1:
            clear_proc = 'ResetMasterBracket'
            insert_proc = 'InsertMasterBracketData'
            params = []

        # convert the picks string to a dictionary
        if 'user_picks' in kwargs:
            user_picks_dict = kwargs['user_picks']
            upset_bonus_dict = kwargs['upset_bonus']
        else:
            user_picks_dict = ast.literal_eval( request.values['user_picks'] )
            upset_bonus_dict = ast.literal_eval( request.values['upset_bonus'] )

        # clear data
        if user_picks_dict:
            self.__db.insert(proc = clear_proc, params = params)

        # loop through the game data and insert it
        for game_id in user_picks_dict:
            team_id = user_picks_dict[game_id]
            upset_bonus_data = upset_bonus_dict[game_id]
            game_id = int(game_id)

            self.debug(f"working with game {game_id} :: {team_id} : did user pick upset {upset_bonus_data}")

            # insert user's game' picks
            params = [
                user_id,
                team_id,
                game_id,
                upset_bonus_data
            ]

            self.__db.insert(proc = insert_proc, params = params)

            # set the game/team relationship
            if is_admin == 1 and int(game_id) < 63:
                # figure out the next game the winner will play in
                game_id = self.set_next_game(int(game_id))
                #self.debug(f"next game is {game_id}")

                game_data = self.__db.query(proc = 'GetTeamsGame', params = [game_id])
                #self.debug(f"working on game {game_id} for team {team_id}")

                if len(game_data) == 0:
                    self.__db.insert(proc = 'AddTeamsGame', params = [game_id, team_id, team_id]) 
                else:
                    self.__db.update(proc = 'UpdateTeamsGame', params = [game_id, team_id])


    def score_all_brackets(self):
        '''Score all user brackets. This is called after each admin bracket update'''
        self.debug('ScoreAllBrackets')
        self.__db.update(proc = 'ScoreAllBrackets', params = [])

        # calculate best possible scores now
        # TODO: fix bugs but removing for now
        # self.precalculate_best_possible_scores()

    def precalculate_best_possible_scores(self, **kwargs):
        '''Precalculate the best possible scores for all users since doing this on the fly is slow'''

        # get all pools
        pools = self.__db.query(proc = 'GetAllPools', params = [])
        
        # bracket types
        #bracket_types = ['normal', 'sweetSixteen']
        bracket_types = ['normal']

        # loop through each pool
        for pool in pools:
            pool_name = pool['poolName']
            
            if pool_name == 'admin' or pool['seedBonusScoring'] == 1:
                continue

            self.debug(f"working woth {pool_name}")

            # loop through each bracket type for each pool
            for bracket_type in bracket_types:
                bracket_type += 'Bracket'
                
                # get pool status, standings and remaining teams for bracket by type
                pool_status = self.__pool.check_pool_status(bracket_type)

                standings_data = self.__db.query(
                    proc = 'Standings',
                    params = [
                        pool_status['is_open'],
                        pool_name,
                        bracket_type
                    ]
                )

                remaining_teams_data = self.__db.query(
                    proc = 'RemainingTeams',
                    params = [
                        pool_name,
                        bracket_type
                    ]
                )

                # get the best possible score for each bracket type
                if bracket_type == 'normalBracket':
                    #remaining_teams_data = remaining_teams_data_full
                    best_possible_data = self.__db.query(
                        proc = 'BestPossibleScore',
                        params = [
                            1,
                            pool_name
                        ]
                    )
                else:
                    #remaining_teams_data = remaining_teams_data_sweet_sixteen
                    best_possible_data = self.__db.query(
                        proc = 'BestPossibleScore',
                        params = [
                            3,
                            pool_name
                        ]
                    )

                calculated_results = self.calculate_best_possible_scores(
                    standings_data = standings_data,
                    best_possible_data = best_possible_data,
                    remaining_teams_data = remaining_teams_data
                )
                
                for data in calculated_results:
                    self.__db.query(proc = 'UpdateBestPossibleScore', params = [
                        data['bestPossibleScore'],
                        data['userID']
                    ])
            
    def calculate_best_possible_scores(self, **kwargs):
        '''
        Calculate the best possible scores left for each user
        
        Some of the variable case names are mixed here as that is how they were previously coming from the DB, this can be addressed later
        '''

        standings_data = kwargs['standings_data']
        remaining_teams_data = kwargs['remaining_teams_data']

        # best possible data
        best_possible_data = kwargs['best_possible_data']
        adjusted_score = best_possible_data[0]['adjustedScore']

        # build standings lookup table
        array_index = 0
        standings_lookup = defaultdict(dict)
        incorrect_picks = defaultdict(dict)

        self.debug("calculate_best_possible_scores")
        self.debug(f"best_possible_data {best_possible_data}")
        self.debug(f"adjusted_score {adjusted_score}")
        self.debug(f"standings_data {standings_data}")
        self.debug(f"remaining_teams_data {remaining_teams_data}")
        self.debug(" ")

        # get cached score data
        score_data_key = 'xx'
        stored_score_data = self.__redis_client.get(score_data_key)

        if stored_score_data is None:
            stored_score_data = {}
        else:
            stored_score_data = json.loads(stored_score_data)

        for data in standings_data:
            token = data['userDisplayToken']
            standings_lookup[token] = array_index
            incorrect_picks[token] = {}
            data['bestPossibleScore'] = int(adjusted_score)

            array_index += 1

        # figure out the best possible score remaining for each user
        for data in remaining_teams_data:
            token = data['userDisplayToken']
            team_name = data['teamName']
            index = standings_lookup[token]

            self.debug(f"working with game {data ['gameID']}")
            

            # user pick is wrong so set the wrong team so we can follow it to the final four
            # team['pickCSS'] = stored_score_data[ data ['gameID'] ][ data ['teamID'] ]['css']
            if data ['gameID'] in stored_score_data and stored_score_data[ data ['gameID'] ][ data ['teamID'] ]['css'] == 'incorrectPick':
                incorrect_picks[token][team_name] = 1;     
                standings_data[index]['bestPossibleScore'] -= data['gameRoundScore']
    
            # this is an incorrect final four pick so decrement the total of correct teams left
            if data['userPick'] == '' and token in incorrect_picks and team_name in incorrect_picks[token]:
                self.debug(f"user pick is wrong {data['userPick']}")
                standings_data[index]['bestPossibleScore'] -= data['gameRoundScore']

        self.debug(f"xxxx {standings_data}")
        return standings_data
   
    def get_start_dates(self):
        '''Get the start dates for the rounds'''

        config = configparser.ConfigParser()
        config.read("site.cfg")

        redis_host = config.get('REDIS', 'REDIS_HOST')
        redis_port = config.get('REDIS', 'REDIS_PORT')
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            decode_responses=True
        )

        results = r.get('dates')
        return json.loads(results)

    def score_brackets_automatically(self):
        '''Call SportsRadar and get scores from completed games'''

        teams = Teams()
        result = teams.get_team_data(setup = 0)
        scored_picks = result['score_data']
        upset_bonus = result['upset_data']
        tie_breaker_points = result['tie_breaker_points']

        self.process_pick_data(
            is_admin = 1,
            user_picks = scored_picks,
            upset_bonus = upset_bonus,
            action = 'edit',
            edit_user_token = self.__user.get_admin_edit_token(),
            tie_breaker_points = tie_breaker_points
        )

        self.score_all_brackets()
        self.clear_redis_cache()
        
        return {"result": "success"}

    def clear_redis_cache(self):
        '''Clear Redis of cached data'''

        self.__redis_client.delete('base_team_data0')
        self.__redis_client.delete('base_team_data1')
        self.__redis_client.delete('yyyyy')
        self.__redis_client.delete('yy')
        self.__redis_client.delete('master_bracket_picks')
