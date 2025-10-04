import unittest
from bus_tracker import *

class TestRescrape(unittest.TestCase):

    def test_get_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn,"failed to connect to DB")

        cursor = conn.cursor()
        cursor.execute("SELECT 1,2,3,4,5")
        result = cursor.fetchall()
        self.assertEqual(result[0][3],4,"The query result should be 3")

        cursor.close()
        conn.close()

    def test_start_new_trip(self):
        
        pass

if __name__ == "__main__":
    unittest.main()