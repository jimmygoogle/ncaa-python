import unittest
import datetime
from mysql_python import MysqlPython

class NcaaTestCase(unittest.TestCase):
    """Tests for my app"""

    def test_01_could_not_connect_to_db(self):
        """Can I connect to DB? (no)"""
        connect_mysql = MysqlPython(host='', user='', password='', database='')
        self.assertEqual(len(connect_mysql.errors), 1)

    def test_02_could_connect_to_db(self):
        """Can I connect to DB? (yes)"""
        connect_mysql = MysqlPython()
        self.assertEqual(len(connect_mysql.errors), 0)
        connect_mysql.close()

    def test_03_get_pool(self):
        """Can we find a pool?"""
        connect_mysql = MysqlPython()
        
        # find our test pool     
        result = connect_mysql.query(proc='PoolInfo', params=['test'])
        self.assertEqual(len(result), 1)

        connect_mysql.close()

    def test_04_cant_get_pool(self):
        """Can we find a non existent pool?"""
        connect_mysql = MysqlPython()      
        
        # look for a non existent pool   
        result = connect_mysql.query(proc='PoolInfo', params=['sarsdfasdf'])
        self.assertEqual(len(result), 0)

        connect_mysql.close()
    
    def test_05_is_pool_open(self):
        """Is the pool open for submissions?"""
        connect_mysql = MysqlPython()
        
        # open pool for test
        connect_mysql.update(proc='OpenPool')

        # check pool status
        result = connect_mysql.query(proc='PoolStatus')
        self.assertEqual(result[0]['poolOpen'], 1)

        connect_mysql.close()     
        
    def test_06_is_pool_closed(self):
        """Have the games begun?"""
        connect_mysql = MysqlPython()
        
        # close pool for test
        connect_mysql.update(proc='ClosePool')

        # check pool status
        result = connect_mysql.query(proc='PoolStatus')
        self.assertEqual(result[0]['poolOpen'], 0)

        connect_mysql.close()
   
    def test_07_is_sweet16_pool_open(self):
        """Is the Sweet pool open?"""
        connect_mysql = MysqlPython()
        
        # open sweet 16 pool for test
        connect_mysql.update(proc='OpenSweet16Pool')

        # check pool status
        result = connect_mysql.query(proc='PoolStatus')
        self.assertEqual(result[0]['sweetSixteenPoolOpen'], 1)

        connect_mysql.close()     
        
    def test_07_is_sweet16_pool_closed(self):
        """Has the Sweet 16 started?"""
        connect_mysql = MysqlPython()
        
        # close sweet 16 pool for test
        connect_mysql.update(proc='CloseSweet16Pool')

        # check pool status
        result = connect_mysql.query(proc='PoolStatus')
        self.assertEqual(result[0]['sweetSixteenPoolOpen'], 0)

        connect_mysql.close()

if __name__ == '__main__':
    unittest.main()