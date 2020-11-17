from flask import request, jsonify
from project.ncaa import Ncaa
from project.pool import Pool
from project.mysql_python import MysqlPython

class Standings(Ncaa):
    '''Standings class that will pull and show standings for the brackets in a defined pool'''

    def __init__(self, **kwargs):
        self.__db = MysqlPython()
        self.__pool = Pool()

    def get_standings(self, **kwargs):
        '''Get standings data for the pool'''

        bracket_type = kwargs['bracket_type'] + 'Bracket'        
        pool_name = self.__pool.get_pool_name()
        pool_status = self.__pool.check_pool_status(bracket_type)

        # fetch the user standings
        data = self.__db.query(proc = 'Standings', params = [pool_status['is_open'], pool_name, bracket_type])
        
        # get number of games played to see if there are games left
        # this will help determine if we show the best possible score column in the standings
        result = self.__db.query(proc = 'AreThereGamesLeft', params = [])
        games_left = result[0]['status']

        # we are using the seed bonus scoring just ignore the best possible score
        pool_info = self.__pool.get_pool_info()
        if pool_info['seedBonusScoring'] == 1:
            games_left = 0

        return (data, games_left)