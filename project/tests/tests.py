import unittest
import datetime
from flask import current_app
from flask.cli import with_appcontext
from project import create_app
from project import mysql_python

class NcaaTestClass(unittest.TestCase):
    """Tests for my app"""

    def __init__(self, *args, **kwargs):
        super(NcaaTestClass, self).__init__(*args, **kwargs)
        
        self.app = create_app(is_testing = 1) 
       
    def setup_db(self):
        '''Set up a DB connection for the test'''

        db = mysql_python.MysqlPython(
            connection = 1,
            hostname = 'localhost',
            user = 'root',
            password = '',
            database = 'MarchMadness',
            charset = 'utf8mb4',
            auto_commit = True
        )
        db.get_db()

        return db  
 
    def test_01_could_not_connect_to_db(self):
        """Can I connect to DB? (no)"""

        with self.app.app_context():
            db = mysql_python.MysqlPython(
                connection = 1,
                hostname = 'localhost',
                user = 'abc',
                password = '123',
                database = '',
                charset = 'utf8mb4',
                auto_commit = True
            )
            db.get_db() 

            self.assertEqual(len(db.errors), 1)  
#
    def test_02_could_connect_to_db(self):
        """Can I connect to DB? (yes)"""

        with self.app.app_context():
            db = self.setup_db()
            self.assertEqual(len(db.errors), 0)        

    def test_03_get_pool(self):
        """Can we find a pool?"""

        # find our test pool 
        with self.app.app_context():
            db = self.setup_db()
            result = db.query(proc='PoolInfo', params=['test'])
            self.assertEqual(len(result), 1)

    def test_04_cant_get_pool(self):
        """Can we find a non existent pool?"""

        # look for a non existent pool
        with self.app.app_context():
            db = self.setup_db()   
            result = db.query(proc='PoolInfo', params=['sarsdfasdf'])
            self.assertEqual(len(result), 0)

    def test_05_is_pool_open(self):
        """Is the pool open for submissions?"""

        # open pool for test
        with self.app.app_context():
            db = self.setup_db()   
            db.update(proc='OpenPool')

            # check pool status
            result = db.query(proc='PoolStatus')
            self.assertEqual(result[0]['poolOpen'], 1)
 
    def test_06_is_pool_closed(self):
        """Have the games begun?"""

        # close pool for test
        with self.app.app_context():
            db = self.setup_db()   
            db.update(proc='ClosePool')
    
            # check pool status
            result = db.query(proc='PoolStatus')
            self.assertEqual(result[0]['poolOpen'], 0)     
   
    def test_07_is_sweet16_pool_open(self):
        """Is the Sweet pool open?"""

        # open sweet 16 pool for test
        with self.app.app_context():
            db = self.setup_db()   
        
            db.update(proc='OpenSweet16Pool')
    
            # check pool status
            result = db.query(proc='PoolStatus')
            self.assertEqual(result[0]['sweetSixteenPoolOpen'], 1)

if __name__ == '__main__':
    unittest.main()