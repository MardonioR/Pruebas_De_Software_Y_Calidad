"""
Módulo de pruebas unitarias para la capa de servicios (HotelSystem).
Cumple con PEP8 y busca alta cobertura de código.
"""

import unittest
import json
from datetime import date
from pathlib import Path

# Importamos las clases de tu implementación
from hotel_system.models import Hotel, Customer, Reservation
from hotel_system.services import HotelSystem, NotFoundError, ValidationError

class TestHotelSystem(unittest.TestCase):
    """Pruebas para las operaciones CRUD y de lógica de negocio."""

    def setUp(self):
        """
        Prepara el entorno creando archivos JSON temporales con listas
        (como lo espera JsonStore) antes de cada prueba.
        """
        # Definir rutas temporales
        self.hotels_file = Path("test_hotels.json")
        self.customers_file = Path("test_customers.json")
        self.reservations_file = Path("test_reservations.json")

        # Inyectar datos iniciales válidos (Listas de diccionarios)
        self.initial_hotels = [
            {
                "hotel_id": "H1",
                "name": "Hotel Plaza",
                "city": "CDMX",
                "total_rooms": 10
            }
        ]
        self.hotels_file.write_text(json.dumps(self.initial_hotels), encoding="utf-8")
        
        # Iniciar archivos vacíos para clientes y reservaciones
        self.customers_file.write_text("[]", encoding="utf-8")
        self.reservations_file.write_text("[]", encoding="utf-8")

        # Instanciar el sistema con los archivos de prueba
        self.system = HotelSystem(
            hotels_file=self.hotels_file,
            customers_file=self.customers_file,
            reservations_file=self.reservations_file
        )

    def tearDown(self):
        """Limpia los archivos temporales después de cada prueba."""
        self.hotels_file.unlink(missing_ok=True)
        self.customers_file.unlink(missing_ok=True)
        self.reservations_file.unlink(missing_ok=True)

    # ==========================================
    # PRUEBAS DE HOTELES (Req 2.1)
    # ==========================================

    def test_create_hotel_success(self):
        """Prueba la creación de un nuevo hotel."""
        new_hotel = Hotel("H2", "Resort Playa", "Cancun", 50)
        self.system.create_hotel(new_hotel)
        
        # Validar usando el método display_hotel
        retrieved = self.system.display_hotel("H2")
        self.assertEqual(retrieved.name, "Resort Playa")
        self.assertEqual(retrieved.total_rooms, 50)

    def test_create_hotel_duplicate(self):
        """Prueba que no se pueda crear un hotel con ID duplicado."""
        duplicate_hotel = Hotel("H1", "Otro Nombre", "Mty", 20)
        with self.assertRaises(ValidationError):
            self.system.create_hotel(duplicate_hotel)

    def test_delete_hotel_success(self):
        """Prueba la eliminación exitosa de un hotel sin reservaciones."""
        self.system.delete_hotel("H1")
        
        # Si intentamos buscarlo, debe lanzar NotFoundError
        with self.assertRaises(NotFoundError):
            self.system.display_hotel("H1")

    def test_modify_hotel_success(self):
        """Prueba la modificación de atributos de un hotel."""
        updated_hotel = self.system.modify_hotel("H1", city="Monterrey", total_rooms=15)
        self.assertEqual(updated_hotel.city, "Monterrey")
        self.assertEqual(updated_hotel.total_rooms, 15)
        # El nombre debe mantenerse igual
        self.assertEqual(updated_hotel.name, "Hotel Plaza")
    
    # ==========================================
    # PRUEBAS DE CLIENTES (Req 2.2)
    # ==========================================

    def test_create_customer_success(self):
        """Prueba la creación de un nuevo cliente."""
        new_customer = Customer("C1", "Mardonio Roman", "mardonio@email.com")
        self.system.create_customer(new_customer)
        
        retrieved = self.system.display_customer("C1")
        self.assertEqual(retrieved.full_name, "Mardonio Roman")
        self.assertEqual(retrieved.email, "mardonio@email.com")

    def test_delete_customer_not_found(self):
        """Prueba que intentar borrar un cliente que no existe lance error."""
        with self.assertRaises(NotFoundError):
            self.system.delete_customer("C-INEXISTENTE")

    # ==========================================
    # PRUEBAS DE RESERVACIONES (Req 2.3)
    # ==========================================

    def test_create_reservation_success(self):
        """Prueba la creación exitosa de una reservación validando disponibilidad."""
        # 1. Preparar: Necesitamos un cliente en el sistema (el hotel 'H1' ya está por el setUp)
        customer = Customer("C1", "Karen Martell", "karen@email.com")
        self.system.create_customer(customer)

        # 2. Ejecutar: Crear reservación de 2 habitaciones
        check_in = date(2026, 3, 10)
        check_out = date(2026, 3, 15)
        
        reservation = self.system.create_reservation(
            hotel_id="H1",
            customer_id="C1",
            check_in=check_in,
            check_out=check_out,
            rooms=2
        )

        # 3. Validar: Que se haya creado con los datos correctos
        self.assertIsInstance(reservation, Reservation)
        self.assertEqual(reservation.hotel_id, "H1")
        self.assertEqual(reservation.rooms, 2)

    def test_create_reservation_invalid_dates(self):
        """Prueba la validación de fechas (check-out antes del check-in)."""
        # Intentar que el check_out sea ANTES del check_in
        check_in = date(2026, 3, 15)
        check_out = date(2026, 3, 10) # <-- Fecha inválida lógicamente
        
        with self.assertRaises(ValidationError) as context:
            self.system.create_reservation(
                hotel_id="H1",
                customer_id="C1",
                check_in=check_in,
                check_out=check_out
            )
        
        # Opcional: validar que el mensaje de error sea el exacto que programaste
        self.assertEqual(str(context.exception), "check_out must be after check_in")

    def test_create_reservation_not_enough_rooms(self):
        """Prueba la validación de sobrecupo en el hotel."""
        self.system.create_customer(Customer("C1", "Cliente Test", "test@test.com"))
        
        # El Hotel H1 creado en el setUp() solo tiene 10 habitaciones.
        # Intentamos reservar 15.
        with self.assertRaises(ValidationError) as context:
            self.system.create_reservation(
                hotel_id="H1",
                customer_id="C1",
                check_in=date(2026, 4, 1),
                check_out=date(2026, 4, 5),
                rooms=15 # <-- Supera las 10 disponibles
            )
        
        self.assertEqual(str(context.exception), "Not enough rooms available")

    # ==========================================
    # PRUEBAS DE TOLERANCIA A FALLOS (Req 5)
    # ==========================================

    def test_jsonstore_invalid_data_execution_continues(self):
        """
        Prueba que si un archivo tiene un elemento válido y otro corrupto,
        el programa descarta el malo, carga el bueno y NO hace crash.
        """
        # Sobrescribimos el archivo con 1 hotel bueno y 1 con datos faltantes
        mixed_data = [
            {"hotel_id": "H-GOOD", "name": "Bueno", "city": "GDL", "total_rooms": 5},
            {"hotel_id": "H-BAD", "name": "Malo"} # Falta city y total_rooms (Lanza KeyError en from_dict)
        ]
        self.hotels_file.write_text(json.dumps(mixed_data), encoding="utf-8")
        
        # Instanciamos de nuevo para forzar la lectura
        system_test = HotelSystem(self.hotels_file, self.customers_file, self.reservations_file)
        
        # El hotel bueno debió cargar exitosamente
        good_hotel = system_test.display_hotel("H-GOOD")
        self.assertEqual(good_hotel.city, "GDL")
        
        # El hotel malo no debió cargar, lanzando NotFoundError al buscarlo
        with self.assertRaises(NotFoundError):
            system_test.display_hotel("H-BAD")

    # ==========================================
    # PRUEBAS FALTANTES DE HOTELES
    # ==========================================

    def test_modify_hotel_invalid_rooms(self):
        """Prueba que no se puedan asignar habitaciones negativas al modificar."""
        with self.assertRaises(ValidationError):
            self.system.modify_hotel("H1", total_rooms=-5)

    def test_modify_hotel_not_found(self):
        """Prueba modificar un hotel que no existe."""
        with self.assertRaises(NotFoundError):
            self.system.modify_hotel("H-FALSO", name="No existo")

    def test_delete_hotel_with_reservations(self):
        """Prueba que no se pueda borrar un hotel si tiene reservas activas."""
        self.system.create_customer(Customer("C_TEST", "Test", "t@t.com"))
        self.system.create_reservation(
            hotel_id="H1", customer_id="C_TEST", 
            check_in=date(2026, 5, 1), check_out=date(2026, 5, 5)
        )
        with self.assertRaises(ValidationError) as context:
            self.system.delete_hotel("H1")
        self.assertEqual(str(context.exception), "Cannot delete hotel with active reservations")

    # ==========================================
    # PRUEBAS FALTANTES DE CLIENTES
    # ==========================================

    def test_modify_customer_success(self):
        """Prueba modificar los datos de un cliente."""
        self.system.create_customer(Customer("C2", "Viejo Nombre", "v@v.com"))
        updated = self.system.modify_customer("C2", full_name="Nuevo Nombre")
        self.assertEqual(updated.full_name, "Nuevo Nombre")
        self.assertEqual(updated.email, "v@v.com") # El email no debió cambiar

    def test_modify_customer_not_found(self):
        """Prueba modificar un cliente que no existe."""
        with self.assertRaises(NotFoundError):
            self.system.modify_customer("C-FALSO", full_name="N/A")

    def test_delete_customer_success(self):
        """Prueba borrar un cliente exitosamente."""
        self.system.create_customer(Customer("C_DEL", "Borrar", "b@b.com"))
        self.system.delete_customer("C_DEL")
        with self.assertRaises(NotFoundError):
            self.system.display_customer("C_DEL")

    def test_delete_customer_with_reservations(self):
        """Prueba que no se pueda borrar un cliente si tiene reservas activas."""
        self.system.create_customer(Customer("C_RES", "Reserva", "r@r.com"))
        self.system.create_reservation(
            hotel_id="H1", customer_id="C_RES", 
            check_in=date(2026, 6, 1), check_out=date(2026, 6, 5)
        )
        with self.assertRaises(ValidationError):
            self.system.delete_customer("C_RES")

    # ==========================================
    # PRUEBAS FALTANTES DE RESERVACIONES
    # ==========================================

    def test_create_reservation_invalid_rooms(self):
        """Prueba que no se pueda reservar 0 o menos habitaciones."""
        self.system.create_customer(Customer("C1", "Test", "t@t.com"))
        with self.assertRaises(ValidationError):
            self.system.create_reservation(
                hotel_id="H1", customer_id="C1", 
                check_in=date(2026, 5, 1), check_out=date(2026, 5, 5), rooms=0
            )

    def test_create_reservation_missing_ids(self):
        """Prueba que lance error si el hotel o cliente no existen."""
        self.system.create_customer(Customer("C_OK", "Test", "t@t.com"))
        
        # Hotel no existe
        with self.assertRaises(NotFoundError):
            self.system.create_reservation(
                hotel_id="H-FALSO", customer_id="C_OK", 
                check_in=date(2026, 5, 1), check_out=date(2026, 5, 5)
            )
            
        # Cliente no existe
        with self.assertRaises(NotFoundError):
            self.system.create_reservation(
                hotel_id="H1", customer_id="C-FALSO", 
                check_in=date(2026, 5, 1), check_out=date(2026, 5, 5)
            )

    def test_cancel_reservation_success(self):
        """Prueba cancelar una reservación y el wrapper cancel_reservation_for_hotel."""
        self.system.create_customer(Customer("C_CANC", "Canc", "c@c.com"))
        
        # Usamos el wrapper reserve_room para probarlo también
        res = self.system.reserve_room(
            hotel_id="H1", customer_id="C_CANC", 
            check_in=date(2026, 8, 1), check_out=date(2026, 8, 5)
        )
        
        # Cancelamos usando el wrapper
        self.system.cancel_reservation_for_hotel(res.reservation_id)
        
        # Si intentamos cancelarla de nuevo, ya no debería existir
        with self.assertRaises(NotFoundError):
            self.system.cancel_reservation(res.reservation_id)
    
if __name__ == '__main__':
    unittest.main()
