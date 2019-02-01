from flask import request, jsonify
from project.ncaa_class import Ncaa
from project.bracket_class import Bracket
from project.pool_class import Pool
from project.mysql_python import MysqlPython
from project import session
from collections import defaultdict

class Standings(Bracket):
    '''Standings class that will pull and show standings for the brackets in a defined pool'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        self.__pool = Pool()

    def get_standings(self, **kwargs):
        '''Get standings data for the pool'''

        bracket_type = kwargs['bracket_type'] + 'Bracket'        
        pool_name = self.__pool.get_pool_name()
        pool_status = self.__pool.check_pool_status(bracket_type)

        # set the round id to calculate the best possible score from
        round_id = 3
        if kwargs['bracket_type'] == 'normal':
            round_id = 1
        
        # calculate best possible score for each user 
        best_possible_data = self.__db.query(proc = 'BestPossibleScore', params = [round_id])
        
        # get the remaining games
        remaining_teams_data = self.__db.query(proc = 'RemainingTeams', params = [pool_name, bracket_type])   
        
        # fetch the user standings
        standings_data = self.__db.query(proc = 'Standings', params = [pool_status['is_open'], pool_name, bracket_type])
        
        # get number of games played to see if there are games left
        # this will help determine if we show the best possible score column in the standings
        result = self.__db.query(proc = 'AreThereGamesLeft', params = [])
        games_left = result[0]['status']

        data = self.calculate_best_possible_scores(standings_data = standings_data, best_possible_data = best_possible_data, remaining_teams_data = remaining_teams_data)
        
        return (data, games_left)

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