"""Cryptographic identity generation for PET."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import uuid4

from nacl.encoding import Base64Encoder, RawEncoder
from nacl.public import PrivateKey


@dataclass(slots=True)
class GeneratedKeyPair:
    """Container for a generated UUID and X25519 key pair."""

    uuid: str
    private_key: Any
    public_key: Any


class KeyManager:
    """Generate UUIDs and X25519 key pairs."""

    def generate_uuid(self) -> str:
        """Generate a new UUID string."""

        return str(uuid4())

    def generate_key_pair(self) -> GeneratedKeyPair:
        """Generate a UUID and X25519 key pair."""

        private_key = PrivateKey.generate()
        return GeneratedKeyPair(
            uuid=self.generate_uuid(),
            private_key=private_key,
            public_key=private_key.public_key,
        )

    def encode_private_key(self, private_key: Any) -> str:
        """Encode a private key for credential storage."""

        return private_key.encode(encoder=Base64Encoder).decode("utf-8")

    def encode_public_key(self, public_key: Any) -> str:
        """Encode a public key for SQLite storage."""

        return public_key.encode(encoder=Base64Encoder).decode("utf-8")

    def public_key_fingerprint(self, public_key: Any) -> str:
        """Return a short fingerprint for display."""

        public_key_bytes = public_key.encode(encoder=RawEncoder)
        return sha256(public_key_bytes).hexdigest()[:16].upper()
