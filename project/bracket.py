from flask import request, jsonify, current_app
from project.ncaa import Ncaa
from project.user import User
from project.pool import Pool
from project.email import send_confirmation_email
from project.mysql_python import MysqlPython
from project.mongo import Mongo
from collections import defaultdict
import ast
import configparser
from project.paypal_client import PayPalClient
from paypalcheckoutsdk.orders import OrdersGetRequest
from paypalhttp import HttpError

class Bracket(Ncaa):
    '''Bracket class to get/set bracket information for a user'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        self.__pool = Pool()
        self.__user = User()
        self.__paypal = PayPalClient()

    def get_base_teams(self):
        '''Get base teams data for display'''
        
        return self.__db.query(proc = 'GetBaseTeams', params = [])

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

        return self.get_user_bracket_for_display(is_admin = 1, user_token = None, action = 'view', bracket_type = 'normalBracket')

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
                    'gameID': 0
                })

        # get the picks from the DB
        user_picks = self.__db.query(proc = proc, params = params)
        
        # handle missing picks from the the master bracket by using the empty bracket and filling in the missing picks
        if is_admin:
            for pick in user_picks:
                admin_picks[pick['gameIDCalc']] = {
                    'gameID': pick['gameID'],
                    'teamID': pick['teamID'],
                    'seedID': pick['seedID'],
                    'teamName': pick['teamName'],
                    'pickCSS': '',
                }

            user_picks = admin_picks 

        return user_picks   
    
    def get_user_bracket_for_display(self, **kwargs):
        '''Get user picks and information so we can display their bracket'''

        action = kwargs['action']
        is_admin = kwargs['is_admin']
        user_token = kwargs['user_token']
        bracket_type = kwargs['bracket_type']

        pool_name = ''
        if is_admin:
            pool_name = self.__pool.get_admin_pool_name()
        else: 
            pool_name = self.__pool.get_pool_name()

        # calculate best possible score for each user
        user_data = []

        # get the user picks
        user_picks = self.get_user_picks(is_admin = is_admin, user_token = user_token)

        # if this is a sweet 16 bracket fill in the 2 previous rounds from master 
        if bracket_type == 'sweetSixteenBracket':    
            master_bracket_picks = self.__db.query(proc = 'MasterBracket', params = [])
            user_picks = master_bracket_picks + user_picks

        # set styling for incorrect picks
        incorrect_picks = {}
        for pick in user_picks:
            team_id = pick['teamID']

            if pick['pickCSS'] == 'incorrectPick':
                incorrect_picks[team_id] = 1;

            if pick['pickCSS'] == '' and team_id in incorrect_picks:
                pick['pickCSS'] = 'incorrectPick'

        # get the base teams (top 64)
        team_data = self.get_base_teams()

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
 
        return {
            'team_data': team_data, 
            'user_picks': user_picks, 
            'user_info': user_info, 
            'bracket_display_name': bracket_display_name
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
            if kwargs['action'] == 'add':
                
                url = request.url_root
                token = self.__user.get_edit_token()
                bracket_type_label = request.values['bracket_type_label']

                results = send_confirmation_email.s(
                    token = token,
                    url = url,
                    pool_name = self.__pool.get_pool_name(),
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

    def process_pick_data(self, **kwargs):
        '''Process the user picks and add them to the DB'''

        user_picks = request.values['user_picks']

        # figure out if we are editing the master bracket since we call different procedures
        is_admin = 0
        if 'is_admin' in kwargs and kwargs['is_admin'] is not None and kwargs['is_admin'] != 0 :
            is_admin = 1

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

        # clear data
        self.__db.insert(proc = clear_proc, params = params)

        # convert the picks string to a dictionary
        user_picks_dict = ast.literal_eval(user_picks)

        # loop through the game data and insert it
        for game_id in user_picks_dict:
            team_id = user_picks_dict[game_id]

            # insert user's game' picks
            self.__db.insert(proc = insert_proc, params = [
                user_id,
                team_id,
                game_id
            ])

    def score_all_brackets(self):
        '''Score all user brackets. This is called after each admin bracket update'''

        self.__db.update(proc = 'ScoreAllBrackets', params = [])
        
        # calculate best possible scores now
        self.precalculate_best_possible_scores()

    def precalculate_best_possible_scores(self, **kwargs):
        '''Precalculate the best possible scores for all users since doing this on the fly is slow'''

        # get the best possible score for each bracket type
        best_possible_data_full = self.__db.query(proc = 'BestPossibleScore', params = [1])
        best_possible_data_sweet_sixteen = self.__db.query(proc = 'BestPossibleScore', params = [3])
        
        # get all pools
        pools = self.__db.query(proc = 'GetAllPools', params = [])
        
        # bracket types
        bracket_types = ['normal', 'sweetSixteen']

        # loop through each pool
        for pool in pools:
            pool_name = pool['poolName']
            
            if pool_name == 'admin':
                continue

            # loop through each bracket type for each pool
            for bracket_type in bracket_types:
                bracket_type += 'Bracket'
                
                # get pool status, standings and remaining teams for bracket by type
                pool_status = self.__pool.check_pool_status(bracket_type)
                standings_data = self.__db.query(proc = 'Standings', params = [pool_status['is_open'], pool_name, bracket_type])
                remaining_teams_data = self.__db.query(proc = 'RemainingTeams', params = [pool_name, bracket_type])
    
                if bracket_type == 'normalBracket':
                    #remaining_teams_data = remaining_teams_data_full
                    best_possible_data = best_possible_data_full
                else:
                    #remaining_teams_data = remaining_teams_data_sweet_sixteen
                    best_possible_data = best_possible_data_sweet_sixteen
                
                calculated_results = self.calculate_best_possible_scores(standings_data = standings_data, best_possible_data = best_possible_data, remaining_teams_data = remaining_teams_data)
                
                for data in calculated_results:
                    self.__db.query(proc = 'UpdateBestPossibleScore', params = [data['bestPossibleScore'], data['userID']])
            
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
        array_index = 0;
        standings_lookup = defaultdict(dict)
        incorrect_picks = defaultdict(dict)

        for data in standings_data:
            token = data['userDisplayToken']
            standings_lookup[token] = array_index
            incorrect_picks[token] = {}
            data['bestPossibleScore'] = adjusted_score

            array_index += 1

        # figure out the best possible score remaining for each user
        for data in remaining_teams_data:
            token = data['userDisplayToken']
            team_name = data['teamName']
            index = standings_lookup[token]

            # user pick is wrong so set the wrong team so we can follow it to the final four
            if data['userPick'] == 'incorrectPick':
                incorrect_picks[token][team_name] = 1;     
                standings_data[index]['bestPossibleScore'] -= data['gameRoundScore']
    
            # this is an incorrect final four pick so decrement the total of correct teams left
            if data['userPick'] == '' and token in incorrect_picks and team_name in incorrect_picks[token]:
                standings_data[index]['bestPossibleScore'] -= data['gameRoundScore']

        return standings_data
   
    def get_start_dates(self):
        '''Get the start dates for the rounds'''
        
        mongodb = Mongo()
        
        config = configparser.ConfigParser()
        config.read("site.cfg")
        
        date_collection_name = config.get('DATES', 'MONGODB_COLLECTION')
        
        results = mongodb.query(collection_name = date_collection_name, query = {})
        return results

    def check_user_payment(self, order_id):
        '''Check that the user's order ID is in fact valid'''

        status = False
        try:
            request = OrdersGetRequest(order_id)
            self.__paypal.client.execute(request)
            status = True
        except IOError as ioe:
            self.debug(ioe)

        return status
