import unittest
import datetime
from mysql_python import MysqlPython

class NcaaTestClass(unittest.TestCase):
    """Tests for my app"""

    def __init__(self, *args, **kwargs):
        super(NcaaTestClass, self).__init__(*args, **kwargs)

        self.db = MysqlPython()   
        
    def test_01_could_not_connect_to_db(self):
        """Can I connect to DB? (no)"""

        connect_mysql = MysqlPython(host = '', user = '', password = '', database = '', pool_name = 'test', pool_size = 1)
        self.assertEqual(len(connect_mysql.errors), 1)    

    def test_02_could_connect_to_db(self):
        """Can I connect to DB? (yes)"""

        self.assertEqual(len(self.db.errors), 0)        

    def test_03_get_pool(self):
        """Can we find a pool?"""

        # find our test pool     
        result = self.db.query(proc='PoolInfo', params=['test'])
        self.assertEqual(len(result), 1)

    def test_04_cant_get_pool(self):
        """Can we find a non existent pool?"""

        # look for a non existent pool   
        result = self.db.query(proc='PoolInfo', params=['sarsdfasdf'])
        self.assertEqual(len(result), 0)

    def test_05_is_pool_open(self):
        """Is the pool open for submissions?"""

        # open pool for test
        self.db.update(proc='OpenPool')

        # check pool status
        result = self.db.query(proc='PoolStatus')
        self.assertEqual(result[0]['poolOpen'], 1)
 
    def test_06_is_pool_closed(self):
        """Have the games begun?"""

        # close pool for test
        self.db.update(proc='ClosePool')

        # check pool status
        result = self.db.query(proc='PoolStatus')
        self.assertEqual(result[0]['poolOpen'], 0)     
   
    def test_07_is_sweet16_pool_open(self):
        """Is the Sweet pool open?"""

        # open sweet 16 pool for test
        self.db.update(proc='OpenSweet16Pool')

        # check pool status
        result = self.db.query(proc='PoolStatus')
        self.assertEqual(result[0]['sweetSixteenPoolOpen'], 1)

if __name__ == '__main__':
    unittest.main()