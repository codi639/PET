"""Password hashing and verification for PET."""

from __future__ import annotations

import secrets

from argon2.exceptions import VerifyMismatchError, VerificationError
from argon2.low_level import Type, hash_secret, verify_secret


class PasswordManager:
    """Hash passwords and verify them with Argon2id."""

    def __init__(self) -> None:
        self.time_cost = 3
        self.memory_cost = 64 * 1024
        self.parallelism = 4
        self.hash_len = 32
        self.salt_len = 16

    def hash_password(self, password: str) -> str:
        """Return an Argon2id password hash for the provided password."""

        salt = secrets.token_bytes(self.salt_len)
        hashed = hash_secret(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            hash_len=self.hash_len,
            type=Type.ID,
        )
        return hashed.decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Return True when the password matches the stored hash."""

        try:
            return verify_secret(
                hash=password_hash.encode("utf-8"),
                secret=password.encode("utf-8"),
                type=Type.ID,
            )
        except (VerifyMismatchError, VerificationError, ValueError):
            return False
