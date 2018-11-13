import mysql.connector, sys

from collections import OrderedDict

class MysqlPython(object):

    def __init__(self, host='localhost', user='root', password='', database='MarchMadness'):
        self.__host = host
        self.__user = user
        self.__password = password
        self.__database = database
        self.errors = []
        
        dbconfig = {
          'host': self.__host,
          'database': self.__database,
          'user': self.__user,
          'password': self.__password,
        }
        
        try:
            self.__connection = mysql.connector.connect(pool_name = 'ncaa_pool', pool_size = 32, **dbconfig)

        except mysql.connector.Error as error:
            print(f"Could not connect {error}")
            self.errors.append(error)

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

            cursor = self.__connection.cursor(dictionary=True)
            cursor.callproc(kwargs['proc'], kwargs['params'])

            # return result set as an array of dictionaries
            for result in cursor.stored_results():
                for row in result:
                    results.append(dict(zip(result.column_names,row)))

        except mysql.connector.Error as error:
            print(f"Failed to execute stored procedure: {error}")
            self.errors.append(error)
        
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
            cursor = self.__connection.cursor(dictionary=True)

            if 'params' not in kwargs:
                kwargs['params'] = []

            # execute write and return last insert id
            cursor.callproc(kwargs['proc'], kwargs['params'])
            last_insert_id = cursor.lastrowid

        except mysql.connector.Error as error:
            print(f"Failed to execute stored procedure: {error}")
            self.errors.append(error)

        return last_insert_id
        
    def query(self, **kwargs):
        '''Wrapper for __execute_procedure'''

        return self._execute_procedure(**kwargs)

    def update(self, **kwargs):
        '''Wrapper for _execute_write_procedure used for updating data'''

        return self._execute_procedure(**kwargs)

    def insert(self, **kwargs):
        '''Wrapper for _execute_write_procedure used for inserting data'''

        return self._execute_write_procedure(**kwargs)        

    def close(self):
        '''Close DB connection'''

        self.__connection.close()
