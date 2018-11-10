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
        result = connect_mysql.query(proc='PoolInfo', params=['test'])
        self.assertEqual(len(result), 1)
        connect_mysql.close()

    def test_03_cant_get_pool(self):
        """Can we find a non existent pool?"""
        connect_mysql = MysqlPython()         
        result = connect_mysql.query(proc='PoolInfo', params=['sarsdfasdf'])
        self.assertEqual(len(result), 0)
        connect_mysql.close()
        
if __name__ == '__main__':
    unittest.main()