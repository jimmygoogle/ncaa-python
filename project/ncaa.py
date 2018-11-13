from mysql_python import MysqlPython
from flask import request
from project import session
import sys

connect_mysql = MysqlPython()

class Ncaa(object):
    
    def __init__(self):
        pass
    
    def set_pool_name(self, pool_name):
        '''Validate pool name and then set it for use in the application'''

        result = connect_mysql.query(proc='PoolInfo', params=[pool_name])
        
        status = 0;
        # we found our pool so set a cookie
        if len(result):
            status = 1
            
            # set pool name in the session
            session['pool_name'] = pool_name         

        return status
    
    def get_pool_name(self):
        '''sdfsd'''

        # try and get pool name from session
        pool_name = session.get('pool_name')
        self.deug(f"pool name is {pool_name}")
        
        return pool_name

    def check_pool_status(self, pool_type='normalBracket'):
        '''Get current pool status'''
        
        result = connect_mysql.query(proc='PoolStatus')
        
        if pool_type == 'normalBracket':
            status = result[0]['poolOpen']
        else:
            status = result[0]['sweetSixteenPoolOpen']
        
        return status
    
    def get_standings(self, **kwargs):
        '''Get standings'''

        bracket_type = kwargs['bracket_type'] + 'Bracket'        
        pool_name = kwargs['pool_name']
        pool_status = self.check_pool_status(bracket_type)
            
        return connect_mysql.query(proc='Standings', params=[pool_status, pool_name, bracket_type])

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)

