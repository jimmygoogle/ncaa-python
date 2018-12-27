from project.mysql_python import MysqlPython
from flask import request
from project import session, app
import sys
import hashlib
import time
import re
from collections import defaultdict



class Ncaa(object):
    
    def __init__(self):
        self.pool_name = ''
        
        self.db = MysqlPython()
    
    def set_pool_name(self, pool_name):
        '''Validate pool name and then set it for use in the application'''

        self.debug(f"inside set_pool_name with {pool_name}")
        result = self.db.query(proc='PoolInfo', params=[pool_name])
        self.debug(result)
        status = 0;
        # we found our pool so set a cookie
        if len(result):
            status = 1
            
            # set pool name in the session
            session['pool_name'] = pool_name
            self.debug(f"pool name is set in the session as {session['pool_name']}")

        return status
    
    def get_pool_name(self):
        '''Get the pool name from the session'''

        # try and get pool name from session
        pool_name = session.get('pool_name')
        self.debug(f"pool name is {pool_name}")
        
        return pool_name

    def check_pool_status(self, bracket_type=None):
        '''Get current pool status'''
        
        result = self.db.query(proc='PoolStatus')
        self.debug(result)
        status = {
            'normalBracket': result[0]['poolOpen'],
            'sweetSixteenBracket': result[0]['sweetSixteenPoolOpen']
        }
        
        if bracket_type is None:
            return status
        else:
            return status[bracket_type]

    def get_standings(self, **kwargs):
        '''Get standings data for the pool'''

        bracket_type = kwargs['bracket_type'] + 'Bracket'        
        pool_name = self.get_pool_name()
        pool_status = self.check_pool_status(bracket_type)

        # set the round id to calculate the best possible score from
        round_id = 3
        if kwargs['bracket_type'] == 'normal':
            round_id = 1
        
        # calculate best possible score for each user 
        best_possible_data = self.db.query(proc='BestPossibleScore', params=[round_id])
        
        # get the remaining games
        remaining_teams_data = self.db.query(proc='RemainingTeams', params=[pool_name, bracket_type])   
        
        # fetch the user standings
        standings_data = self.db.query(proc='Standings', params=[pool_status, pool_name, bracket_type])
        
        # get number of games played
        games_left = self.db.query(proc='AreThereGamesLeft', params=[])

        data = self.calculate_best_possible_scores(standings_data=standings_data, best_possible_data=best_possible_data, remaining_teams_data=remaining_teams_data)
        
        return (data, 1)

    def calculate_best_possible_scores(self, **kwargs):
        '''
        Calculate the best possible scores left for each user
        
        Some of the variable case names are mixed here as that is how they were previously coming from the DB, this can be addressed later
        
        '''

        standings_data = kwargs['standings_data']
        remaining_teams_data = kwargs['remaining_teams_data']

        # best possible data
        best_possible_data = kwargs['best_possible_data']
        best_possible_score = best_possible_data[0]['bestPossibleScore']
        adjusted_score = best_possible_data[0]['adjustedScore']

        # build standings lookup table
        array_index = 0;
        standings_lookup = defaultdict(dict)
        incorrect_picks = defaultdict(dict)
        
        self.debug(f"adjusted score is {adjusted_score}")
        self.debug(f"best possible score is {best_possible_score}")

        for data in standings_data:
            token = data['userDisplayToken']
            standings_lookup[token] = array_index
            incorrect_picks[token] = {}
            data['bestPossibleScore'] = adjusted_score

            array_index += 1
        
        self.debug(standings_data[0])
        self.debug(remaining_teams_data[0])
        
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
            if data['userPick'] == '' and token in incorrect_picks and incorrect_picks[token][team_name]:
                standings_data[index]['bestPossibleScore'] -= data['gameRoundScore']

        return standings_data

    def get_user_bracket_for_display(self, **kwargs):
        '''Get standings data for the pool'''

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
            user_info = self.db.query(proc='GetUserByDisplayToken', params=[user_token])
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
        
    def set_user_edit_token(self, **kwargs):
        '''
        Creates a token string to be encoded from the time, pool name, user email, username, bracket type and display type.
        This combo ensures a unique token for every user
        '''
        
        token = [time.time(), session['pool_name'], kwargs[email_address], kwargs['username'], kwargs['bracket_type'], 'edit'];
        return set_token(token.join('.'))
    
    def set_user_display_token(self, **kwargs):
        '''
        Creates a token string to be encoded from the time, pool name, user email, username, bracket type and display type.
        This combo ensures a unique token for every user
        '''
        
        token = [time.time(), session['pool_name'], kwargs[email_address], kwargs['username'], kwargs['bracket_type'], 'display'];
        return set_token(token.join('.'))
    
    def set_token(self, string):
        '''Creates an md5 hash from string parameter'''
        
        h = hashlib.new('ripemd160')
        h.update(string)
        return h.hexdigest()
    
    def set_user_bracket_name(self, username):
        '''
        Fixes the usernmame for display.
        
        If the username doesnt end in an 's' append one for the bracket name
        ex: Jim -> Jim's
        ex: Balls stays Balls'
        '''
        
        # get rid of spaces at the end of the user name and append '
        username = re.sub(r'\s+$', '', username)
        username += "'"

        # append 's' at the end of the string if the string doesnt already end with "'s"
        if not re.search(r"s'$", username):
            username += 's'

        return username
    
    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)

