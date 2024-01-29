from flask import app, request, jsonify, g
from project.ncaa import Ncaa
import configparser
import datetime

class SportRadar(Ncaa):
    '''Setup calls to SportsRadar'''

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.year = str(datetime.datetime.now().year - 1)
        self.api_key = config.get('SPORTSRADAR', 'API_KEY')

        base_url = 'https://api.sportradar.us/ncaamb'
        type = 'trial'
        version = 'v7'
        locale = 'en'

        self.sportsradar_url = f"{base_url}/{type}/{version}/{locale}"

        Ncaa.__init__(self)
