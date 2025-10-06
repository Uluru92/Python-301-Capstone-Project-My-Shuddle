import unittest
from bus_tracker import *

class TestBusTracker(unittest.TestCase):

    def setUp(self):
        """Get ready to start every test"""
        self.original_bus = getattr(app_state, "current_bus", None)
        app_state.current_bus = None  # Make sure it starts empty
    
    def tearDown(self):
        """restores default value"""
        app_state.current_bus = self.original_bus

    def test_get_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn,"failed to connect to DB")

        cursor = conn.cursor()
        cursor.execute("SELECT 1,2,3,4,5")
        result = cursor.fetchall()
        self.assertEqual(result[0][3],4,"The query result should be 3")

        cursor.close()
        conn.close()

    def test_current_bus_uses_default_plate(self):
        """Verifica que se use la placa por defecto si no se pasa argumento"""
        start_new_trip()
        self.assertEqual(app_state.current_bus.plate, "BUS123")

    def test_start_new_trip_current_bus_is_instance_of_Bus(self):
        """Verifica que start_new_trip cree un objeto Bus"""
        plate = "TEST123"
        start_new_trip(plate=plate)

        # test if current_bus is not None
        self.assertIsNotNone(app_state.current_bus)

        # test if new instancia is a Bus object
        self.assertIsInstance(app_state.current_bus, Bus)

        # test if bus is using the correct plate passed as argument
        self.assertEqual(app_state.current_bus.plate, "TEST123")

        # Check if locations is a list
        self.assertIsInstance(app_state.current_bus.locations, list)

        # Check if trip_file path targets to /trips
        self.assertTrue(app_state.current_trip_file.startswith("trips/"))
        self.assertIn(plate, app_state.current_trip_file)

        # Check if trip_in_progress is True
        self.assertTrue(app_state.trip_in_progress)

        # Check if /trips exists
        self.assertTrue(os.path.exists("trips"))

    def test_save_current_trip(self):
        
        pass

if __name__ == "__main__":
    unittest.main()