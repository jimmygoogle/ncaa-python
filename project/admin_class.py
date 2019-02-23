from flask import request, jsonify, redirect
from project.ncaa_class import Ncaa
from project.polls_class import Polls
from project.user_class import User
from project.mysql_python import MysqlPython
from project.mongo import Mongo
from project import session
import ast
import configparser
import re
import hashlib
import binascii

class Admin(Ncaa):
    '''Performs admin functions such as creating a new bracket or editing the master bracket'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        self.__mongo = Mongo()

        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__edit_token = config.get('DEFAULT', 'ADMIN_EDIT_TOKEN')
        self.__collection_name = config.get('DATES', 'MONGODB_COLLECTION')
        self.__admin_login_salt = config.get('DEFAULT', 'ADMIN_LOGIN_SALT')

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
        
        # reset and repull top 25 poll data
        self.reset_and_pull_poll_data()

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

    def reset_and_pull_poll_data(self):
        '''Clear and repull AP and USA Today Top 25 polls'''

        self.debug('reset_and_pull_poll_data')
        # delete the top 25 poll data
        polls = Polls()
        polls.reset_polls_collection()
        
        # get the new AP poll data
        polls.get_ap_poll_data()
        polls.get_usa_today_poll_data()
        
        return 1
   
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
        self.__db.insert(proc = 'AddNewPool', params = [request.values['pool_name']])
        errors = self.__db.errors

        if len(errors) > 0:
            status = str(errors[0])
        else:
            status = 'ok'

        # TODO: this needs better error handling
        return jsonify({
            'status' : status,
        })
        
    def process_admin_login(self):
        '''Process admin token to see if they are allowed to login'''
               
        password = request.values['admin_password']
        self.debug(f"entered password is {password}")
        
        results = self.__db.query(proc = 'CheckAdminPassword', params = [])
        self.debug(results[0]['userPassword'])
  
        hashed_password = self.hash_password(password)
        self.debug(f"hashed_password is  {hashed_password}")
        
        if results[0]['userPassword'] == hashed_password:
            session['admin_logged_in'] = 1
            return 1

        return 0
    
    def is_logged_in(self):
        '''Check if we are logged in'''
        
        if 'admin_logged_in' in session:
            status = 1
        else:
            status = 0

        return status
 
    def hash_password(self, password):
        '''Hash a password for admin'''

        config = configparser.ConfigParser()
        config.read("site.cfg")
        
        salt = config.get('DEFAULT', 'ADMIN_LOGIN_SALT').encode('utf-8')
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')       
 