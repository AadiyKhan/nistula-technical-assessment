from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Property
from .repositories.user_repository import UserRepository
from .security import hash_password


def seed_demo_data(session: Session) -> None:
    demo_properties = [
        Property(
            property_id="villa-b1",
            name="Villa B1",
            city="Assagao, North Goa",
            base_rate="INR 18,000 per night",
            max_guests=6,
            availability="April 20-24: Available",
            context_text=(
                "Bedrooms: 3 | Max guests: 6 | Private pool: Yes\n"
                "Check-in: 2pm | Check-out: 11am\n"
                "Extra guest: INR 2,000 per night per person\n"
                "WiFi password: Nistula@2024\n"
                "Caretaker: Available 8am to 10pm\n"
                "Chef on call: Yes, pre-booking required\n"
                "Cancellation: Free up to 7 days before check-in"
            ),
        ),
        Property(
            property_id="suite-c3",
            name="Suite C3",
            city="Candolim, Goa",
            base_rate="INR 12,000 per night",
            max_guests=4,
            availability="Available most weekdays",
            context_text=(
                "Bedrooms: 2 | Max guests: 4 | Shared pool: Yes\n"
                "Check-in: 3pm | Check-out: 11am\n"
                "Parking: 1 car included\n"
                "Late checkout: subject to availability"
            ),
        ),
    ]
    session.add_all(demo_properties)
    seed_demo_users(session)
    session.commit()


def seed_demo_users(session: Session) -> None:
    user_repo = UserRepository(session)
    if not user_repo.get_by_username("owner@nistula.local"):
        user_repo.create_user(
            username="owner@nistula.local",
            full_name="Nistula Owner",
            password_hash=hash_password("owner12345"),
            role="owner",
        )
    if not user_repo.get_by_username("manager@nistula.local"):
        user_repo.create_user(
            username="manager@nistula.local",
            full_name="Nistula Manager",
            password_hash=hash_password("manager12345"),
            role="manager",
        )
    if not user_repo.get_by_username("support@nistula.local"):
        user_repo.create_user(
            username="support@nistula.local",
            full_name="Nistula Support",
            password_hash=hash_password("support12345"),
            role="support",
        )
    session.commit()