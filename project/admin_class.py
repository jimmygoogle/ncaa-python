from flask import request, jsonify
from project.ncaa_class import Ncaa
from project.mysql_python import MysqlPython
import ast
import configparser

class Admin(Ncaa):
    '''Performs admin functions such as creating a new bracket or editing the master bracket'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        
        # get edit token
        config = configparser.ConfigParser()
        config.read("site.cfg")
        self.__edit_token = config.get('DEFAULT', 'ADMIN_EDIT_TOKEN')
        
    def get_edit_token(self):
        '''Get edit token'''
            
        return self.__edit_token
    
    def initialize_new_bracket(self):
        '''Delete all the existing team data and insert new team data'''

        # delete all the current team data
        self.__db.insert(proc='DeleteTeams', params=[])
        
        # convert the data to a dictionary
        team_data = ast.literal_eval(request.values['team_data'])

        for team_name in team_data:
            # insert the team data for each game
            seed_id = team_data[team_name]['seed_id']
            game_id = team_data[team_name]['game_id']
            
            self.__db.insert(proc='InsertTeamsData', params=[team_name, seed_id, game_id])

        # TODO: this needs be error handling
        return jsonify({
            'status' : 1,
        })