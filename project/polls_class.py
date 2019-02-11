from flask import jsonify
from project.ncaa_class import Ncaa
from collections import OrderedDict
from pymongo import MongoClient
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

        # the polls run off of the year of the start of the season
        self.__year = str(datetime.datetime.now().year - 1)
    
    def get_usa_today_poll_data(self):
        '''Call Sports Radar API and get USA Today Poll data'''
        
        #self.debug(self.__usa_today_url)
        url = re.sub(r'YEAR', self.__year, self.__usa_today_url)

        usa_today_response = requests.get(url)        
#        self.debug(usa_today_response.content)
        return usa_today_response.json()

        
        
    def get_ap_poll_data(self):
        '''Call Sports Radar API and get AP Poll data'''
        
        self.debug(self.__ap_url)
        url = re.sub(r'YEAR', self.__year, self.__ap_url)

        ap_response = requests.get(url)
        #self.debug(ap_response.json())
        #time.sleep(5)    

        client = MongoClient('mongodb://localhost:27017')
        
        #self.debug(ap_response.json())
        
        db = client['ncaa']
        polls = db['polls']
        polls.drop()

        result = polls.insert(ap_response.json())

        myquery = {"poll.alias": "AP" }
        
        mydoc = polls.find(myquery)

        for x in mydoc:
            self.debug(f"booyah {x}")

        for x in polls.find():
            self.debug(x)