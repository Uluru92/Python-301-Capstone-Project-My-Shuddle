import unittest
from bus_tracker import *

class TestBusTracker(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de cada test"""
        # Guardamos el estado original por si hay que restaurarlo luego
        self.original_bus = getattr(app_state, "current_bus", None)
        app_state.current_bus = None  # Asegura que empiece vacío
    
    def tearDown(self):
        """Se ejecuta después de cada test"""
        # Restauramos el estado original
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

if __name__ == "__main__":
    unittest.main()