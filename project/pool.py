from flask import app, request, jsonify, g, flash
from project.ncaa import Ncaa
from project.confirmation_email import send_contact_us_email
from project.mysql_python import MysqlPython
from project import session
import ast
import traceback

class Pool(Ncaa):
    '''Pool class to get/set the user pool. The pool name defines where the user their bracket data will live'''

    def __init__(self):
        self.__db = MysqlPython()

        # set pool specific attributes
        self.pool_name = ''

        Ncaa.__init__(self)

    def set_pool_name(self, pool_name):
        '''Validate pool name and then set it for use in the application'''

        result = self.__db.query(proc = 'PoolInfo', params = [pool_name])
        #self.debug(result)

        status = 0
        # we found our pool so set a cookie
        if len(result):
            status = 1
            
            # set pool name in the session
            session['pool_name'] = pool_name
            session['pool_id'] = result[0]['poolID']
            #self.debug(f"pool name is set in the session as {session['pool_name']} with pool id {session['pool_id']}")

        return status
    
    def get_pool_name(self):
        '''Get the pool name from the session'''

        # try and get pool name from session
        pool_name = session.get('pool_name')
        return pool_name

    def get_admin_pool_name(self):
        '''Get the pool name from the admin'''

        return 'admin'

    def validate_pool_name(self, pool_name):
        '''Check the pool name passed in the request against the defined pools in the DB'''
        
        result = self.__db.query(proc = 'PoolInfo', params = [pool_name])
        
        status = 0
        if len(result) > 0:
            status = 1
            self.set_pool_name(pool_name)
        
        return status     
    
    def are_pools_open(self):
        '''Check if either pool is open'''

        status = self.check_pool_status('any')
        return status['is_open']

    def check_pool_status(self, bracket_type=None):
        '''Get current status of all pools'''
        
        result = self.__db.query(proc = 'PoolStatus')
        #self.debug(result)

        # figure out if either pool is open for easier checks        
        one_pool_is_open = 0
        if result[0]['poolOpen'] or result[0]['sweetSixteenPoolOpen'] :
            one_pool_is_open = 1

        status = {
            'normalBracket': {'is_open': result[0]['poolOpen'], 'closing_date_time': result[0]['poolCloseDateTime']},
            'sweetSixteenBracket': {'is_open': result[0]['sweetSixteenPoolOpen'], 'closing_date_time': result[0]['sweetSixteenCloseDateTime'] },
            'any': {'is_open': one_pool_is_open }
        }

        if bracket_type is None:
            return status
        else:
            return status[bracket_type]

    def get_pool_info(self):
        '''Get all info for pool'''

        pool_name = self.get_pool_name()
        result = self.__db.query(proc = 'PoolInfo', params = [pool_name])
        #self.debug(result)
        return result[0]

    def get_pool_round_score(self):
        '''Get scoring for pool'''
        return {}

        pool_name = self.get_pool_name()
        result = self.__db.query(proc = 'GetPoolRoundScore', params = [pool_name])
        return result[0]

    def send_contact_email(self, **kwargs):
        '''Send email to admin'''

        flash('Your request has been submitted. You will receive a response shortly.')
        send_contact_us_email.s(**kwargs).apply_async(seconds=10)
