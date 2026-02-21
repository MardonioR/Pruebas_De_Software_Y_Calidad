"""
Módulo de pruebas unitarias para los modelos de dominio.
Verifica la correcta instanciación y serialización de datos.
"""

import unittest
from datetime import date

# Importamos las clases directamente desde models.py
from hotel_system.models import Hotel, Customer, Reservation


class TestHotelModel(unittest.TestCase):
    """Pruebas para el modelo de datos Hotel."""

    def setUp(self):
        """Prepara datos de prueba para los tests de Hotel."""
        self.hotel = Hotel(
            hotel_id="H001",
            name="Hotel Central",
            city="Guadalajara",
            total_rooms=100
        )
        self.hotel_dict = {
            "hotel_id": "H001",
            "name": "Hotel Central",
            "city": "Guadalajara",
            "total_rooms": 100
        }

    def test_hotel_creation(self):
        """Prueba que el dataclass asigne los atributos correctamente."""
        self.assertEqual(self.hotel.hotel_id, "H001")
        self.assertEqual(self.hotel.name, "Hotel Central")
        self.assertEqual(self.hotel.total_rooms, 100)

    def test_hotel_to_dict(self):
        """Prueba la serialización del objeto Hotel a diccionario."""
        result = self.hotel.to_dict()
        self.assertEqual(result, self.hotel_dict)

    def test_hotel_from_dict(self):
        """Prueba la creación de un objeto Hotel desde un diccionario."""
        new_hotel = Hotel.from_dict(self.hotel_dict)
        self.assertIsInstance(new_hotel, Hotel)
        self.assertEqual(new_hotel.hotel_id, "H001")
        self.assertEqual(new_hotel.total_rooms, 100)

    def test_hotel_from_dict_missing_key(self):
        """Prueba que lance KeyError si falta un campo requerido."""
        bad_dict = {"hotel_id": "H002", "name": "Incompleto"}
        with self.assertRaises(KeyError):
            Hotel.from_dict(bad_dict)

    def test_hotel_from_dict_value_error(self):
        """Prueba que lance ValueError si un tipo de dato es incompatible."""
        bad_dict = {
            "hotel_id": "H003",
            "name": "Error Hotel",
            "city": "Monterrey",
            "total_rooms": "cien"  # Esto no se puede convertir a int()
        }
        with self.assertRaises(ValueError):
            Hotel.from_dict(bad_dict)


class TestCustomerModel(unittest.TestCase):
    """Pruebas para el modelo de datos Customer."""

    def setUp(self):
        """Prepara datos de prueba para los tests de Customer."""
        self.customer = Customer(
            customer_id="C001",
            full_name="Juan Perez",
            email="juan@email.com"
        )
        self.customer_dict = {
            "customer_id": "C001",
            "full_name": "Juan Perez",
            "email": "juan@email.com"
        }

    def test_customer_to_dict(self):
        """Prueba la serialización del objeto Customer a diccionario."""
        self.assertEqual(self.customer.to_dict(), self.customer_dict)

    def test_customer_from_dict(self):
        """Prueba la deserialización de un diccionario a objeto Customer."""
        new_customer = Customer.from_dict(self.customer_dict)
        self.assertEqual(new_customer.full_name, "Juan Perez")
        self.assertEqual(new_customer.email, "juan@email.com")


class TestReservationModel(unittest.TestCase):
    """Pruebas para el modelo de datos Reservation."""

    def setUp(self):
        """Prepara datos de prueba para los tests de Reservation."""
        self.check_in_date = date(2026, 3, 1)
        self.check_out_date = date(2026, 3, 5)

        self.reservation = Reservation(
            reservation_id="R001",
            hotel_id="H001",
            customer_id="C001",
            check_in=self.check_in_date,
            check_out=self.check_out_date,
            rooms=2
        )

        # El diccionario debe tener las fechas como strings (formato ISO)
        self.reservation_dict = {
            "reservation_id": "R001",
            "hotel_id": "H001",
            "customer_id": "C001",
            "check_in": "2026-03-01",
            "check_out": "2026-03-05",
            "rooms": 2
        }

    def test_reservation_to_dict(self):
        """Prueba que las fechas se conviertan correctamente a string."""
        result = self.reservation.to_dict()
        self.assertEqual(result, self.reservation_dict)
        # Validar específicamente que la fecha es un string en el dict
        self.assertIsInstance(result["check_in"], str)

    def test_reservation_from_dict(self):
        """Prueba que los strings ISO se conviertan de vuelta a objetos date."""
        new_res = Reservation.from_dict(self.reservation_dict)
        self.assertIsInstance(new_res.check_in, date)
        self.assertEqual(new_res.check_in, self.check_in_date)
        self.assertEqual(new_res.rooms, 2)

    def test_reservation_invalid_date_format(self):
        """Prueba que lance ValueError si la fecha no tiene formato ISO."""
        bad_dict = self.reservation_dict.copy()
        bad_dict["check_in"] = "01-03-2026"  # Formato incorrecto

        with self.assertRaises(ValueError):
            Reservation.from_dict(bad_dict)


if __name__ == '__main__':
    unittest.main()
