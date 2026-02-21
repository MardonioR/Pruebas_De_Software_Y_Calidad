"""
models.py
---
Domain models for the hotel reservation system.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict


@dataclass(frozen=True, slots=True)
class Hotel:
    """Represents a hotel."""

    hotel_id: str
    name: str
    city: str
    total_rooms: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        return {
            "hotel_id": self.hotel_id,
            "name": self.name,
            "city": self.city,
            "total_rooms": self.total_rooms,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Hotel":
        """Deserialize from dict, validating required fields."""
        return Hotel(
            hotel_id=str(data["hotel_id"]),
            name=str(data["name"]),
            city=str(data["city"]),
            total_rooms=int(data["total_rooms"]),
        )


@dataclass(frozen=True, slots=True)
class Customer:
    """Represents a customer."""

    customer_id: str
    full_name: str
    email: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        return {
            "customer_id": self.customer_id,
            "full_name": self.full_name,
            "email": self.email,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Customer":
        """Deserialize from dict, validating required fields."""
        return Customer(
            customer_id=str(data["customer_id"]),
            full_name=str(data["full_name"]),
            email=str(data["email"]),
        )


@dataclass(frozen=True, slots=True)
class Reservation:
    """Represents a reservation between a customer and a hotel."""

    reservation_id: str
    hotel_id: str
    customer_id: str
    check_in: date
    check_out: date
    rooms: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        return {
            "reservation_id": self.reservation_id,
            "hotel_id": self.hotel_id,
            "customer_id": self.customer_id,
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "rooms": self.rooms,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Reservation":
        """Deserialize from dict, validating required fields."""
        return Reservation(
            reservation_id=str(data["reservation_id"]),
            hotel_id=str(data["hotel_id"]),
            customer_id=str(data["customer_id"]),
            check_in=date.fromisoformat(str(data["check_in"])),
            check_out=date.fromisoformat(str(data["check_out"])),
            rooms=int(data["rooms"]),
        )
