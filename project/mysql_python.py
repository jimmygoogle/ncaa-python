from flask import current_app, g
from flask.cli import with_appcontext
#import click#
import mysql.connector, sys
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
#from mysql.connector import pooling
from collections import OrderedDict
import configparser


class MysqlPython(object):

    def __init__(self, **kwargs):
        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.__host = config.get('MYSQL', 'MYSQL_HOST')
        self.__user = config.get('MYSQL', 'MYSQL_USER')
        self.__password = config.get('MYSQL', 'MYSQL_PASSWORD')
        self.__database = config.get('MYSQL', 'MYSQL_DATABASE')
        self.__pool_size = int(config.get('MYSQL', 'MYSQL_POOL_SIZE'))
        self.__database_pool_name = config.get('MYSQL', 'MYSQL_POOL_NAME')
            
        self.__connection = None

        self.errors = []

    def init_app(app):
        app.teardown_appcontext(close_db)

    def get_db(self):
        if 'db' not in g:
            try:
                dbconfig = {
                    'host': self.__host,
                    'database': self.__database,
                    'user': self.__user,
                    'password': self.__password,
                    'charset': 'utf8mb4',
                    'autocommit': True
                }

                g.db = mysql.connector.connect(**dbconfig)

            except Error as error:
                self.debug(f"Could not connect ... {error}")
                self.errors.append(error)
                
        return g.db

    def close_db(e=None):
        db = g.pop('db', None)

        if db is not None:
            db.close()

    def _execute_procedure(self, **kwargs):
        '''Execute a select statement in a procedure and returns the results
        
        Args:
             proc (str): name of procedure to call
             params (array): ordered arguments to pass into procedure
            
        Returns:
            Array of dictionaries with the result of the select statement

        '''

        try:
            results = []
            if 'params' not in kwargs:
                kwargs['params'] = []

            connection = self.get_db()
            #self.debug(f"execute connection id is {connection.connection_id}")
            cursor = connection.cursor(dictionary=True)

            cursor.callproc(kwargs['proc'], kwargs['params'])

            # return result set as an array of dictionaries
            for result in cursor.stored_results():
                for row in result:
                    results.append(dict(zip(result.column_names,row)))

        except mysql.connector.Error as error:
            self.debug(f"Failed to execute stored procedure: {error}")
            self.errors.append(error)

        finally:
            cursor.close()

        return results

    def _execute_write_procedure(self, **kwargs):
        '''Execute a insert/update statement in a procedure and returns the last insert id
        
        Args:
             proc (str): name of procedure to call
             params (array): ordered arguments to pass into procedure
            
        Returns:
            Last insert id from write

        '''

        last_insert_id = 0
        try:
            if 'params' not in kwargs:
                kwargs['params'] = []

            connection = self.get_db()
            #self.debug(f"write connection id is {connection.connection_id}")
            cursor = connection.cursor(dictionary=True)

            # execute write, commit and return last insert id
            cursor.callproc(kwargs['proc'], kwargs['params'])

            for result in cursor.stored_results():
                data = result.fetchall()
                last_insert_id = data[0][0]
                #self.debug(f"last insert id is {last_insert_id}")

        except Error as error:
            self.debug(f"Failed to execute stored procedure: {error}")
            self.errors.append(error)

        finally:
            cursor.close()

        return last_insert_id
        
    def query(self, **kwargs):
        '''Wrapper for __execute_procedure'''

        return self._execute_procedure(**kwargs)

    def update(self, **kwargs):
        '''Wrapper for _execute_write_procedure used for updating data'''
        return self._execute_write_procedure(**kwargs)

    def insert(self, **kwargs):
        '''Wrapper for _execute_write_procedure used for inserting data'''

        return self._execute_write_procedure(**kwargs)        

    def close(self):
        '''Close DB connection'''
        pass
        #self.__connection.close()

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)
