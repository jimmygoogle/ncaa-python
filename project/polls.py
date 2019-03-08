from flask import jsonify
from project.ncaa import Ncaa
from project.mongo import Mongo
from collections import OrderedDict
import requests 
import configparser
import datetime
import re
import time

class Polls(Ncaa):
    '''Get the top 25 teams from USA Today and AP'''
        
    def __init__(self):
        
        config = configparser.ConfigParser()
        config.read("site.cfg")
        
        self.__ap_url = config.get('POLLS', 'AP_URL')
        self.__usa_today_url = config.get('POLLS', 'USA_TODAY_URL')
        self.__collection_name = config.get('POLLS', 'MONGODB_COLLECTION')

        # the polls run off of the year of the start of the season
        self.__year = str(datetime.datetime.now().year - 1)
        
        self.__mongo = Mongo()
    
    def reset_polls_collection(self):
        '''Reset/drop the polls mongodb collection'''

        mongodb = self.__mongo
        self.debug(f"reset collection '{self.__collection_name}'")
        mongodb.drop_collection(collection_name = self.__collection_name)
        
    def get_usa_today_poll_data(self):
        '''Get USA Today Poll data'''
        
        return self.get_api_data(type = 'US')
   
    def get_ap_poll_data(self):
        '''Get AP Poll data'''
        
        return self.get_api_data(type = 'AP')

    def get_api_data(self, **kwargs):
        '''Call Sports Radar API and get Top 25 poll data'''

        #self.reset_polls_collection()
        mongodb = self.__mongo
        
        # try and get results from mongodb
        type = kwargs['type']
        results = mongodb.query(collection_name = self.__collection_name, query = {'poll.alias': type})
        
        # return the data
        if len(results) > 0:
            #self.debug(f"got {type} from mongo")
            return results
        
        # get results from api and store them
        else:
            self.debug(f"getting {type} from api")
            
            # set api url
            if type == 'US':
                api_url = self.__usa_today_url
            else:
                api_url = self.__ap_url 

            # substitute the year in url
            url = re.sub(r'YEAR', self.__year, api_url)
    
            # fetch the data
            ap_response = requests.get(url)
            time.sleep(2)    
            
            # set movement rankings CSS class and insert poll data
            results = self.set_ranking_movements(ap_response.json())
            mongodb.insert(collection_name = self.__collection_name, data = results)

            return results

    def set_ranking_movements(self, rankings):
        '''Set the CSS class based on the ranking of the current week versus the previous week'''

        for data in rankings['rankings']:
            movement = 'none'
            
            # figure out if they moved up, down or not at all
            if 'prev_rank' in data:
                if data['rank'] > data['prev_rank']:
                    movement = 'down'
                elif data['rank'] < data['prev_rank']:
                    movement = 'up'

            data['movement'] = movement
            
        return rankings
