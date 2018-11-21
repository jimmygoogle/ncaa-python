from project.mysql_python import MysqlPython
from flask import request
from project import session, app
import sys
from collections import defaultdict

connect_mysql = MysqlPython()

class Ncaa(object):
    
    def __init__(self):
        pass
    
    def set_pool_name(self, pool_name):
        '''Validate pool name and then set it for use in the application'''

        self.debug(f"inside set_pool_name with {pool_name}")
        result = connect_mysql.query(proc='PoolInfo', params=[pool_name])
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

    def check_pool_status(self, pool_type='normalBracket'):
        '''Get current pool status'''
        
        result = connect_mysql.query(proc='PoolStatus')
        
        if pool_type == 'normalBracket':
            status = result[0]['poolOpen']
        else:
            status = result[0]['sweetSixteenPoolOpen']
        
        return status
    
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
        best_possible_data = connect_mysql.query(proc='BestPossibleScore', params=[round_id])
        
        # get the remaining games
        remaining_teams_data = connect_mysql.query(proc='RemainingTeams', params=[pool_name, bracket_type])   
        
        # fetch the user standings
        standings_data = connect_mysql.query(proc='Standings', params=[pool_status, pool_name, bracket_type])
        
        # get number of games played
        games_left = connect_mysql.query(proc='AreThereGamesLeft', params=[])

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
    
    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)

