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

    def get_db(self):
        '''Make a connection to mongo that will live for the duration of the request'''

        self.debug(f"get_db")
        if 'mongo' not in g:
            client = MongoClient(f"mongodb://{self.__host}:{self.__port}")
            g.mongo = client[self.__database]
 
#        except Error as error:
#            
#            self.debug(f"Could not connect ... {error}")
#            self.errors.append(error)
#            g.mongo = None

        self.debug(g.mongo)
        return g.mongo

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

#        except Error as error:
#            pass
##            self.debug(f"Failed to insert: {error}")
##            self.errors.append(error)


    def query(self, **kwargs):
        '''Get data from the defined collection based on the query param'''
        
        
        #client = MongoClient('mongodb://localhost:27017')
        
        #self.debug(ap_response.json())
        
#        db = client['ncaa']
#        polls = db['polls']
#        polls.drop()
#
#        result = polls.insert(ap_response.json())
#
#        myquery = {"poll.alias": "AP" }
#        
#        mydoc = polls.find(myquery)
#
#        for x in mydoc:
#            self.debug(f"booyah {x}")
#
#        for x in polls.find():
#            self.debug(x)

        # get collection and make a query
        collection = self.get_collection(**kwargs)
        results = collection.find(kwargs['query'])
        
        data = []
        for result in results:
           data.append(result)

#        except Error as error:
#            pass
#            self.debug(f"Failed to query: {error}")
#            self.errors.append(error)

        return data

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)
