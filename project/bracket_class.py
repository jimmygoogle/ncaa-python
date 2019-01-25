from project.user_class import User
from project import session, app, YEAR

class Bracket(User):
    '''Bracket class to get/set bracket information for a user'''

    def __init__(self):
        super().__init__()

    def get_base_teams(self):
        '''Get base teams data for display'''
        
        return self.db.query(proc='GetBaseTeams', params=[])

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
        
        data = self.get_user_bracket_for_display(is_master = 1, user_token = None)
        return data

    def get_user_bracket_for_display(self, **kwargs):
        '''Get user picks and information so we can display their bracket'''

        action = kwargs['action']
        is_master = kwargs['is_master']
        user_token = kwargs['user_token']
        pool_name = self.get_pool_name()
        pool_status = self.check_pool_status()
        
        self.debug(f'Getting data for {user_token}')

        # calculate best possible score for each user
        user_data = []
        
        # if 
        if user_token is not None:
            user_picks = self.db.query(proc='UserDisplayBracket', params=[user_token])

            # set syling for incorrect picks
            incorrect_picks = {}
            for pick in user_picks:
                team_id = pick['teamID']

                if pick['pickCSS'] == 'incorrectPick':
                    incorrect_picks[team_id] = 1;

                if not pick['pickCSS'] and incorrect_picks[team_id]:
                    pick['pickCSS'] = 'incorrectPick'

        else:
            user_picks = self.db.query(proc='MasterBracket', params=[])

            # remove formatting
            for pick in user_picks:
                pick['pickCSS'] = ''

        # get the base teams (top 64)
        team_data = self.get_base_teams()

        # if we have a real user then get some additional info
        if user_token:
            proc = 'GetUserByDisplayToken'
            
            if action == 'edit':
                proc = 'GetUserByEditToken'
 
            user_info = self.db.query(proc=proc, params=[user_token])
            bracket_display_name = self.set_user_bracket_name(user_info[0]['userName'])
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
    
        if not self.are_pools_open():
            error = 'The pool is no longer open.'
            message = ''

        else:
            # process all of the user's picks and put them into the DB
            self.process_pick_data()
            
            # TODO handle errors from processing
            error = ''

            # send confirmation email if this is a new bracket
            if kwargs['action'] == 'add':
                self.send_confirmation_email()
                message = 'Your bracket has been submitted. <br/> Good luck!'
            # set updated message
            else:
                message = 'Your bracket has been updated.'

        return jsonify({
            'message' : message,
            'error': error
        })

    def process_pick_data(self):
        '''Process the user picks and add them to the DV'''

        bracket_type_name = request.values['bracket_type_name']
        email_address = request.values['username']
        username = request.values['bracket_type_name']
        first_name = request.values['first_name']
        tie_breaker_points = request.values['tie_breaker_points']
        user_picks = request.values['user_picks']
        edit_type = request.values['edit_type']

        # add/edit user data:
        user_id = self.update_user_data()
        
        self.debug(f"Working with user {user_id}")

        # convert the picks string to a dictionary
        user_picks_dict = ast.literal_eval(user_picks)

        # loop through the game data and insert it
        for game_id in user_picks_dict:
            team_id = user_picks_dict[game_id]

            # insert user's game' picks
            self.db.insert(proc='InsertBracketData', params=[
                user_id,
                team_id,
                game_id
            ])