"""
services.py
---
Service layer implementing required behaviors.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from hotel_system.models import Customer, Hotel, Reservation
from hotel_system.storage import JsonStore, index_by_id


class NotFoundError(ValueError):
    """Raised when an entity is not found."""


class ValidationError(ValueError):
    """Raised when input validation fails."""


@dataclass
class HotelSystem:
    """Main façade for hotel/customer/reservation operations."""

    hotels_file: Path
    customers_file: Path
    reservations_file: Path

    def __post_init__(self) -> None:
        self._hotels_store = JsonStore(self.hotels_file)
        self._customers_store = JsonStore(self.customers_file)
        self._reservations_store = JsonStore(self.reservations_file)

    # -------------------------
    # Loading helpers
    # -------------------------
    def _load_hotels(self) -> List[Hotel]:
        return self._hotels_store.load_list(item_loader=Hotel.from_dict, item_name="hotel")

    def _load_customers(self) -> List[Customer]:
        return self._customers_store.load_list(
            item_loader=Customer.from_dict,
            item_name="customer",
        )

    def _load_reservations(self) -> List[Reservation]:
        return self._reservations_store.load_list(
            item_loader=Reservation.from_dict,
            item_name="reservation",
        )

    def _save_hotels(self, hotels: List[Hotel]) -> None:
        self._hotels_store.save_list(hotels)

    def _save_customers(self, customers: List[Customer]) -> None:
        self._customers_store.save_list(customers)

    def _save_reservations(self, reservations: List[Reservation]) -> None:
        self._reservations_store.save_list(reservations)

    # -------------------------
    # Hotel behaviors (Req 2.1)
    # -------------------------
    def create_hotel(self, hotel: Hotel) -> None:
        hotels = self._load_hotels()
        by_id = index_by_id(hotels, get_id=lambda h: h.hotel_id)
        if hotel.hotel_id in by_id:
            raise ValidationError(f"Hotel already exists: {hotel.hotel_id}")
        if hotel.total_rooms <= 0:
            raise ValidationError("total_rooms must be > 0")
        hotels.append(hotel)
        self._save_hotels(hotels)

    def delete_hotel(self, hotel_id: str) -> None:
        hotels = self._load_hotels()
        if not any(h.hotel_id == hotel_id for h in hotels):
            raise NotFoundError(f"Hotel not found: {hotel_id}")

        reservations = self._load_reservations()
        if any(r.hotel_id == hotel_id for r in reservations):
            raise ValidationError("Cannot delete hotel with active reservations")

        hotels = [h for h in hotels if h.hotel_id != hotel_id]
        self._save_hotels(hotels)

    def display_hotel(self, hotel_id: str) -> Hotel:
        hotels = self._load_hotels()
        for hotel in hotels:
            if hotel.hotel_id == hotel_id:
                return hotel
        raise NotFoundError(f"Hotel not found: {hotel_id}")

    def modify_hotel(
        self,
        hotel_id: str,
        *,
        name: Optional[str] = None,
        city: Optional[str] = None,
        total_rooms: Optional[int] = None,
    ) -> Hotel:
        hotels = self._load_hotels()
        updated: List[Hotel] = []
        found = False

        for hotel in hotels:
            if hotel.hotel_id != hotel_id:
                updated.append(hotel)
                continue

            found = True
            new_total = hotel.total_rooms if total_rooms is None else int(total_rooms)
            if new_total <= 0:
                raise ValidationError("total_rooms must be > 0")

            updated_hotel = Hotel(
                hotel_id=hotel.hotel_id,
                name=hotel.name if name is None else str(name),
                city=hotel.city if city is None else str(city),
                total_rooms=new_total,
            )
            updated.append(updated_hotel)

        if not found:
            raise NotFoundError(f"Hotel not found: {hotel_id}")

        self._save_hotels(updated)
        return self.display_hotel(hotel_id)

    def reserve_room(
        self,
        *,
        hotel_id: str,
        customer_id: str,
        check_in: date,
        check_out: date,
        rooms: int = 1,
    ) -> Reservation:
        return self.create_reservation(
            hotel_id=hotel_id,
            customer_id=customer_id,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
        )

    def cancel_reservation_for_hotel(self, reservation_id: str) -> None:
        self.cancel_reservation(reservation_id)

    # -------------------------
    # Customer behaviors (Req 2.2)
    # -------------------------
    def create_customer(self, customer: Customer) -> None:
        customers = self._load_customers()
        by_id = index_by_id(customers, get_id=lambda c: c.customer_id)
        if customer.customer_id in by_id:
            raise ValidationError(f"Customer already exists: {customer.customer_id}")
        customers.append(customer)
        self._save_customers(customers)

    def delete_customer(self, customer_id: str) -> None:
        customers = self._load_customers()
        if not any(c.customer_id == customer_id for c in customers):
            raise NotFoundError(f"Customer not found: {customer_id}")

        reservations = self._load_reservations()
        if any(r.customer_id == customer_id for r in reservations):
            raise ValidationError("Cannot delete customer with active reservations")

        customers = [c for c in customers if c.customer_id != customer_id]
        self._save_customers(customers)

    def display_customer(self, customer_id: str) -> Customer:
        customers = self._load_customers()
        for customer in customers:
            if customer.customer_id == customer_id:
                return customer
        raise NotFoundError(f"Customer not found: {customer_id}")

    def modify_customer(
        self,
        customer_id: str,
        *,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Customer:
        customers = self._load_customers()
        updated: List[Customer] = []
        found = False

        for customer in customers:
            if customer.customer_id != customer_id:
                updated.append(customer)
                continue

            found = True
            updated_customer = Customer(
                customer_id=customer.customer_id,
                full_name=customer.full_name if full_name is None else str(full_name),
                email=customer.email if email is None else str(email),
            )
            updated.append(updated_customer)

        if not found:
            raise NotFoundError(f"Customer not found: {customer_id}")

        self._save_customers(updated)
        return self.display_customer(customer_id)

    # -------------------------
    # Reservation behaviors (Req 2.3)
    # -------------------------
    def create_reservation(
        self,
        *,
        hotel_id: str,
        customer_id: str,
        check_in: date,
        check_out: date,
        rooms: int = 1,
        reservation_id: Optional[str] = None,
    ) -> Reservation:
        if rooms <= 0:
            raise ValidationError("rooms must be > 0")
        if check_out <= check_in:
            raise ValidationError("check_out must be after check_in")

        hotels = self._load_hotels()
        customers = self._load_customers()
        reservations = self._load_reservations()

        hotels_by_id: Dict[str, Hotel] = index_by_id(hotels, get_id=lambda h: h.hotel_id)
        customers_by_id: Dict[str, Customer] = index_by_id(
            customers, get_id=lambda c: c.customer_id
        )

        if hotel_id not in hotels_by_id:
            raise NotFoundError(f"Hotel not found: {hotel_id}")
        if customer_id not in customers_by_id:
            raise NotFoundError(f"Customer not found: {customer_id}")

        hotel = hotels_by_id[hotel_id]
        reserved_rooms = sum(
            r.rooms
            for r in reservations
            if r.hotel_id == hotel_id
            and not (check_out <= r.check_in or check_in >= r.check_out)
        )
        available = hotel.total_rooms - reserved_rooms
        if rooms > available:
            raise ValidationError("Not enough rooms available")

        new_reservation = Reservation(
            reservation_id=str(reservation_id or uuid4()),
            hotel_id=hotel_id,
            customer_id=customer_id,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
        )
        reservations.append(new_reservation)
        self._save_reservations(reservations)
        return new_reservation

    def cancel_reservation(self, reservation_id: str) -> None:
        reservations = self._load_reservations()
        if not any(r.reservation_id == reservation_id for r in reservations):
            raise NotFoundError(f"Reservation not found: {reservation_id}")

        reservations = [r for r in reservations if r.reservation_id != reservation_id]
        self._save_reservations(reservations)
