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
            self.__connection = mysql.connector.connect(pool_name = 'ncaa_pool', pool_size = 10, **dbconfig)
        except mysql.connector.Error as error:
            print(f"Could not connect {error}")
            self.errors.append(error)

    def __select(self, **kwargs):
        try:
            cursor = self.__connection.cursor()

            cursor.callproc(kwargs['proc'], kwargs['params'])

            for result in cursor.stored_results():
                results = result.fetchall()

        except mysql.connector.Error as error:
            print(f"Failed to execute stored procedure: {error}")
            self.errors.append(error)
            results = []
        
        return results
        
    def query(self, **kwargs):
        return self.__select(**kwargs)
        
    def __write(self):
        pass

    def update(self):
        pass

    def insert(self):
        pass        

    def close(self):
        self.__connection.close()
