from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Property


class PropertyRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_property(self, property_id: str | None) -> Property:
        if property_id:
            property_row = self.session.get(Property, property_id)
            if property_row:
                return property_row

        fallback = self.session.scalar(select(Property).where(Property.is_active.is_(True)).order_by(Property.property_id))
        if fallback:
            return fallback

        raise LookupError("No property records are available")

    def list_properties(self) -> list[Property]:
        return list(self.session.scalars(select(Property).order_by(Property.name)).all())

    def build_context(self, property_row: Property) -> str:
        parts = [
            f"Property: {property_row.name}",
            f"Property ID: {property_row.property_id}",
        ]
        if property_row.city:
            parts.append(f"City: {property_row.city}")
        if property_row.max_guests is not None:
            parts.append(f"Max guests: {property_row.max_guests}")
        if property_row.base_rate:
            parts.append(f"Base rate: {property_row.base_rate}")
        if property_row.availability:
            parts.append(f"Availability: {property_row.availability}")
        parts.append(property_row.context_text)
        return "\n".join(parts)
