from flask import request, jsonify
from project.ncaa_class import Ncaa
from project.user_class import User
from project.pool_class import Pool
from project.email_class import Email
from project.mysql_python import MysqlPython
from project import session
import ast

class Bracket(Ncaa):
    '''Bracket class to get/set bracket information for a user'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        self.__pool = Pool()
        self.__user = User()
        self.__email = Email()

    def get_base_teams(self):
        '''Get base teams data for display'''
        
        return self.__db.query(proc='GetBaseTeams', params=[])

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

        return self.get_user_bracket_for_display(is_master = 1, user_token = None, action = 'view')

    def get_user_bracket_for_display(self, **kwargs):
        '''Get user picks and information so we can display their bracket'''

        action = kwargs['action']
        is_master = kwargs['is_master']
        user_token = kwargs['user_token']
        pool_name = self.__pool.get_pool_name()
        pool_status = self.__pool.check_pool_status()

        # calculate best possible score for each user
        user_data = []
        
        # there is a user token so pull the user's data
        if user_token is not None:
            self.debug(f'Getting data for {user_token}')
            user_picks = self.__db.query(proc='UserDisplayBracket', params=[user_token])

            # set syling for incorrect picks
            incorrect_picks = {}
            for pick in user_picks:
                team_id = pick['teamID']

                if pick['pickCSS'] == 'incorrectPick':
                    incorrect_picks[team_id] = 1;

                if not pick['pickCSS'] and incorrect_picks[team_id]:
                    pick['pickCSS'] = 'incorrectPick'

        # get master bracket
        else:
            user_picks = self.__db.query(proc='MasterBracket', params=[])

            # remove formatting
            for pick in user_picks:
                pick['pickCSS'] = ''

        # get the base teams (top 64)
        team_data = self.get_base_teams()

        # if we have a real user then get some additional info
        if user_token is not None:
            proc = 'GetUserByDisplayToken'
            
            if action == 'edit':
                proc = 'GetUserByEditToken'
 
            user_info = self.__db.query(proc=proc, params=[user_token])
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
    
        if not self.__pool.are_pools_open():
            error = 'The pool is no longer open.'
            message = ''

        else:
            # process all of the user's picks and put them into the DB
            self.process_pick_data(**kwargs)
            
            # TODO handle errors from processing
            error = ''

            # send confirmation email if this is a new bracket
            if kwargs['action'] == 'add':
                self.__email.send_confirmation_email(token = self.__user.get_edit_token())
                message = 'Your bracket has been submitted. <br/> Good luck!'
            # set updated message
            else:
                message = 'Your bracket has been updated.'

        return jsonify({
            'message' : message,
            'error': error
        })

    def process_pick_data(self, **kwargs):
        '''Process the user picks and add them to the DB'''

        bracket_type_name = request.values['bracket_type_name']
        email_address = request.values['username']
        username = request.values['bracket_type_name']
        first_name = request.values['first_name']
        tie_breaker_points = request.values['tie_breaker_points']
        user_picks = request.values['user_picks']
        edit_type = request.values['edit_type']
        
        # we have an edit token set it so the user can be updated
        if 'edit_user_token' in kwargs:
            self.__user.set_edit_token(kwargs['edit_user_token'])

        # add/edit user data:
        user_id = self.__user.update_user_data()
        
        self.debug(f"Working with user {user_id}")

        # convert the picks string to a dictionary
        user_picks_dict = ast.literal_eval(user_picks)

        # loop through the game data and insert it
        for game_id in user_picks_dict:
            team_id = user_picks_dict[game_id]

            # insert user's game' picks
            self.__db.insert(proc='InsertBracketData', params=[
                user_id,
                team_id,
                game_id
            ])
