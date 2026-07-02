"""PET file header structures for the hybrid encryption engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.recipient import Recipient


@dataclass(slots=True)
class FileHeader:
    """Represent the metadata written before the encrypted file payload."""

    version: int
    algorithm: int
    nonce: bytes
    recipients: list[Recipient] = field(default_factory=list)
