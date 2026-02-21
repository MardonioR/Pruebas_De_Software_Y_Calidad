"""
Punto de entrada principal para ejecutar el Sistema de Reservaciones de Hoteles.
Demuestra la creación, validación y persistencia de datos.
"""

from pathlib import Path
from datetime import date

# Importamos las clases de nuestros módulos
from hotel_system.models import Hotel, Customer
from hotel_system.services import HotelSystem, ValidationError, NotFoundError


def main():
    """Ejecuta un flujo de prueba del sistema de reservaciones."""
    print("=" * 60)
    print("🏨 INICIANDO SISTEMA DE RESERVACIONES")
    print("=" * 60)

    # 1. Configurar las rutas a los archivos JSON (carpeta data/)
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)  # Crea la carpeta si no existe

    # Instanciar el sistema principal
    system = HotelSystem(
        hotels_file=data_dir / "hotels.json",
        customers_file=data_dir / "customers.json",
        reservations_file=data_dir / "reservations.json"
    )

    # 2. Crear un Hotel
    print("\n[1] Registrando Hotel...")
    hotel_demo = Hotel(hotel_id="H001", name="Grand Hotel", city="Guadalajara", total_rooms=50)
    try:
        system.create_hotel(hotel_demo)
        print(f"  ✅ Hotel '{hotel_demo.name}' registrado exitosamente.")
    except ValidationError as error:
        print(f"  ⚠️  Aviso: {error} (El hotel ya estaba registrado)")

    # 3. Crear un Cliente
    print("\n[2] Registrando Cliente...")
    cliente_demo = Customer(
        customer_id="C001", 
        full_name="Ana Gomez", 
        email="ana.gomez@email.com"
    )
    try:
        system.create_customer(cliente_demo)
        print(f"  ✅ Cliente '{cliente_demo.full_name}' registrado exitosamente.")
    except ValidationError as error:
        print(f"  ⚠️  Aviso: {error} (El cliente ya estaba registrado)")

    # 4. Crear una Reservación
    print("\n[3] Procesando Reservación...")
    try:
        reservacion = system.reserve_room(
            hotel_id="H001",
            customer_id="C001",
            check_in=date(2026, 4, 10),
            check_out=date(2026, 4, 15),
            rooms=2
        )
        print(f"  ✅ ¡Reservación confirmada! ID asignado: {reservacion.reservation_id}")
    except ValidationError as error:
        print(f"  ⚠️  No se pudo reservar (Validación): {error}")
    except NotFoundError as error:
        print(f"  ❌  No se pudo reservar (Datos no encontrados): {error}")

    # 5. Consultar y mostrar la información guardada
    print("\n[4] Consultando Base de Datos...")
    try:
        info_hotel = system.display_hotel("H001")
        print(f"  🏨 Información del Hotel: {info_hotel.name} en {info_hotel.city}")
        print(f"  🛏️  Habitaciones Totales: {info_hotel.total_rooms}")

        info_cliente = system.display_customer("C001")
        print(f"  👤 Información del Cliente: {info_cliente.full_name} ({info_cliente.email})")
    except NotFoundError as error:
        print(f"  ❌  Error de consulta: {error}")

    print("\n" + "=" * 60)
    print("Revisa la carpeta 'data/' para ver los archivos JSON generados.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
