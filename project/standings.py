from flask import request, jsonify
import configparser
import redis
import json
from project.ncaa import Ncaa
from project.pool import Pool
from project.mysql_python import MysqlPython

class Standings(Ncaa):
    '''Standings class that will pull and show standings for the brackets in a defined pool'''

    def __init__(self, **kwargs):
        # TODO can i use pool db connection
        self.__db = MysqlPython()
        self.__pool = Pool()

        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__redis_client = redis.Redis(
            host=config.get('REDIS', 'REDIS_HOST'),
            port=config.get('REDIS', 'REDIS_PORT'),
            db=0,
            decode_responses=True
        )

        self.users_per_page = int(config.get('DEFAULT', 'USERS_PER_PAGE'))

    def get_standings_data(self, **kwargs):
        standings_data = self.get_standings_from_cache(**kwargs)
        
        if standings_data is not None and len(standings_data) > 0:
            return standings_data

        kwargs['bracket_type'] += 'Bracket'
        kwargs['pool_name'] = self.__pool.get_pool_name()
        kwargs['pool_status'] = self.__pool.check_pool_status(kwargs['bracket_type'])

        # lets fetch the user standings from the DB
        standings_data = self.__db.query(
            proc = 'Standings',
            params = [
                kwargs['pool_status']['is_open'],
                kwargs['pool_name'],
                kwargs['bracket_type']
            ]
        )

        # set cache
        key = 'yy'
        self.__redis_client.set(key, json.dumps(standings_data))

        return self.get_standings_from_cache(**kwargs)

    def get_standings_from_cache(self, **kwargs):
        key = 'yy'
        standings_data = self.__redis_client.get(key)

        if standings_data is None:
            return []
        
        standings_data = json.loads(standings_data)

        if 'page' in kwargs:
            offset_start = (kwargs['page'] - 1) * kwargs['per_page']
            offset_stop = kwargs['page'] * kwargs['per_page']
        else:
            offset_start = 0
            offset_stop = kwargs['per_page']

        return standings_data

    def games_left(self):
        key = 'yyyyy'
        games_left = self.__redis_client.get(key)

        if games_left is not None:
            return games_left

        result = self.__db.query(proc = 'AreThereGamesLeft', params = [])
        self.__redis_client.set(key, result[0]['status'])
        
        return result[0]['status']

    def get_standings(self, **kwargs):
        '''Get standings data for the pool'''

        # check redis for standings data for `pool_name`
        standings_data = self.get_standings_data(**kwargs)

        # get number of games played to see if there are games left
        # this will help determine if we show the best possible score column in the standings
        games_left = self.games_left()

        # we are using the seed bonus scoring just ignore the best possible score
        # TODO: do we need this now?
        # pool_info = self.__pool.get_pool_info()
        # if pool_info['seedBonusScoring'] == 1:
        #     games_left = 0

        return (standings_data, games_left)
