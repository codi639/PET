"""Identity creation results for PET."""

from __future__ import annotations

from dataclasses import dataclass

from models.user import User


@dataclass(slots=True)
class AccountCreationResult:
    """Return value for a newly created account."""

    user: User
    public_key_fingerprint: str
