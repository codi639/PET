"""User model for PET."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class User:
    """Represent a PET user account."""

    id: int | None
    uuid: str
    username: str
    created_at: str
