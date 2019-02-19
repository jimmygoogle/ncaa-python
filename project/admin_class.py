from flask import request, jsonify
from project.ncaa_class import Ncaa
from project.polls_class import Polls
from project.mysql_python import MysqlPython
from project.mongo import Mongo
import ast
import configparser
import re

class Admin(Ncaa):
    '''Performs admin functions such as creating a new bracket or editing the master bracket'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        self.__mongo = Mongo()

        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__edit_token = config.get('DEFAULT', 'ADMIN_EDIT_TOKEN')
        self.__collection_name = config.get('DATES', 'MONGODB_COLLECTION')

    def reset_dates_collection(self):
        '''Reset/drop the dates mongodb collection'''

        mongodb = self.__mongo
        self.debug(f"reset collection '{self.__collection_name}'")
        mongodb.drop_collection(collection_name = self.__collection_name)
        
    def get_edit_token(self):
        '''Get edit token'''
            
        return self.__edit_token
    
    def initialize_new_bracket(self):
        '''Delete all the existing team data and insert new team data and clear out and repopulate top 25 poll data'''
        
        # delete the top 25 poll data
        polls = Polls()
        polls.reset_polls_collection
        
        # get the new AP poll data
        polls.get_ap_poll_data()
        polls.get_usa_today_poll_data()

        # delete all the current team data
        self.__db.insert(proc='DeleteTeams', params=[])
        
        # convert the data to a dictionary
        team_data = ast.literal_eval(request.values['team_data'])

        for team_name in team_data:
            # insert the team data for each game
            seed_id = team_data[team_name]['seed_id']
            game_id = team_data[team_name]['game_id']
            
            self.__db.insert(proc='InsertTeamsData', params=[team_name, seed_id, game_id])

        # TODO: this needs better error handling
        return jsonify({
            'status' : 1,
        })
        
    def setup_game_start_dates_for_display(self):
        '''Write the game start dates to mongodb'''
            
        # clear out the old data
        self.reset_dates_collection()
        
        # transform data for easier retrieval
        data = ast.literal_eval(request.values['game_dates'])

        dates = []
        for item in data:
            dates.append({item['name']: item['value']})

        # insert new dates
        mongodb = self.__mongo
        mongodb.insert(collection_name = self.__collection_name, data = dates)

        # TODO: this needs better error handling
        return jsonify({
            'status' : 1,
        })

    def setup_pool_open_close_dates(self):
        '''Update pool start/end dates in DB'''

        # update the start/end times
        dates = ast.literal_eval(request.values['pool_dates'])
        self.__db.update(proc = 'UpdatePoolData', params = [dates['normal_close'], dates['sweet_16_open'], dates['sweet_16_close']])

        # TODO: this needs better error handling
        return jsonify({
            'status' : 1,
        })
        
    def add_new_pool(self):
        '''Add new pool to DB'''
            
        # try and add new pool and check to see if it already exists
        data = ast.literal_eval(request.values['pool_name'])
        self.__db.insert(proc = 'AddNewPool', params = [data[0]['value']])
        errors = self.__db.errors

        if len(errors) > 0:
            self.debug('HEYO')
            status = str(errors[0])
        else:
            status = 'ok'

        # TODO: this needs better error handling
        return jsonify({
            'status' : status,
        })
 