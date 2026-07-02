"""Recipient metadata for PET."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Recipient:
    """Represent an encryption recipient and their wrapped AES key."""

    uuid: str
    encrypted_aes_key: bytes
