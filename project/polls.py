from flask import jsonify
from project.sportsradar import SportRadar
from collections import OrderedDict
import requests 
import configparser
import re
import time
import redis
import json

class Polls(SportRadar):
    '''Get the top 25 teams from USA Today and AP'''
        
    def __init__(self):
        SportRadar.__init__(self)

        self.__ap_url = f"{self.sportsradar_url}/polls/AP/{self.year}/rankings.json?api_key={self.api_key}"
        self.__usa_today_url = f"{self.sportsradar_url}/polls/US/{self.year}/rankings.json?api_key={self.api_key}"
        
    def get_usa_today_poll_data(self, force = 0):
        '''Get USA Today Poll data'''
        
        return self.get_api_data(type = 'US',
                                 force = force)
   
    def get_ap_poll_data(self, force = 0):
        '''Get AP Poll data'''
        
        return self.get_api_data(type = 'AP',
                                 force = force)

    def get_api_data(self, **kwargs):
        '''Call Sports Radar API and get Top 25 poll data'''

        config = configparser.ConfigParser()
        config.read("site.cfg")

        redis_host = config.get('REDIS', 'REDIS_HOST')
        redis_port = config.get('REDIS', 'REDIS_PORT')
        r = redis.Redis(host=redis_host, port=redis_port, db=0)

        # try and get results from cache
        type = kwargs['type']
        results = r.get(f"{type}_poll")

        if results:
            results = json.loads(results)

        # return the data
        if not kwargs['force'] and results and len(results) > 0:
            #self.debug(f"got {type} from redis")
            return results
        
        # get results from api and store them
        else:
            self.debug(f"getting {type} from api")
            
            # set api url
            if type == 'US':
                api_url = self.__usa_today_url
            else:
                api_url = self.__ap_url 

            # fetch the data
            ap_response = requests.get(api_url)
            time.sleep(2)    
            
            # set movement rankings CSS class and insert poll data
            results = self.set_ranking_movements(ap_response.json())
            r.set(f"{type}_poll", json.dumps(results))

            return results

    def set_ranking_movements(self, rankings):
        '''Set the CSS class based on the ranking of the current week versus the previous week and add logos'''

        for data in rankings['rankings']:
            movement = 'none'
            
            # figure out if they moved up, down or not at all
            if 'prev_rank' in data:
                if data['rank'] > data['prev_rank']:
                    movement = 'down'
                elif data['rank'] < data['prev_rank']:
                    movement = 'up'

            data['movement'] = movement
            data['logo_name'] = data['market'] + ' ' + data['name']

        return rankings
