from flask import current_app, g
from flask.cli import with_appcontext
from pymongo import MongoClient
from pymongo import errors
import sys
import configparser

class Mongo(object):

    def __init__(self, **kwargs):        
        # get connection from args
        if 'connection' in kwargs:
            self.__host = kwargs['host']
            self.__port = kwargs['port']
            self.__port = kwargs['client']

        # get connection from site.cfg
        else:
            config = configparser.ConfigParser()
            config.read("site.cfg")

            self.__host = config.get('MONGODB', 'MONGODB_HOST')
            self.__port = config.get('MONGODB', 'MONGODB_PORT')
            self.__database = config.get('MONGODB', 'MONGODB_DATABASE')

        self.errors = []
        self.__client = None

    def get_db(self):
        '''Make a connection to mongo that will live for the duration of the request'''

        self.debug(f"get_db")
        if 'mongo' not in g:
            self.__client = MongoClient(f"mongodb://{self.__host}:{self.__port}")
            g.mongo = self.__client[self.__database]

        return g.mongo

    def close_db(self, e=None):
        '''Close connection to mongodb'''
            
        g.pop('mongo', None)

        if self.__client is not None:
            self.__client.close()
        
    def get_collection(self, **kwargs):
        '''Get/create the collection specified'''
        
        collection_name = kwargs['collection_name']
        self.debug(f"get collection '{collection_name}'")
 
        connection = self.get_db()
        return connection[collection_name]

    def drop_collection(self, **kwargs):
        '''Drop the collection'''

        collection = self.get_collection(**kwargs)
        self.debug(collection)
        collection.drop()

    def insert(self, **kwargs):
        '''Insert a record into the collection'''

        data = kwargs['data']

        #try:
        collection = self.get_collection(**kwargs)
        collection.insert(data)


    def query(self, **kwargs):
        '''Get data from the defined collection based on the query param'''

        # get collection and make a query
        collection = self.get_collection(**kwargs)
        results = collection.find(kwargs['query'])
        
        data = []
        for result in results:
           data.append(result)

        return data

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)
