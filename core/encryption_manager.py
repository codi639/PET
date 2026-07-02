"""Hybrid file encryption engine for PET."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from nacl.encoding import Base64Encoder
from nacl.public import PublicKey, SealedBox

from core.database import DatabaseManager
from core.user_manager import UserManager
from models.file_header import FileHeader
from models.recipient import Recipient

PET_MAGIC = b"PET\xae\x42\xf1\x02\x00"
PET_VERSION = 1
ALGORITHM_AES_256_GCM = 1
NONCE_SIZE = 12
AES_KEY_SIZE = 32
AUTH_TAG_SIZE = 16
UUID_LENGTH = 36
RECIPIENT_COUNT_SIZE = 2
ENCRYPTED_KEY_LENGTH_SIZE = 2
CHUNK_SIZE = 64 * 1024


@dataclass(slots=True)
class EncryptionResult:
    """Return value for a successful encryption operation."""

    output_path: Path
    recipient_count: int


class EncryptionManager:
    """Encrypt files for one or more recipients using AES-256-GCM."""

    def __init__(
        self, database_manager: DatabaseManager, user_manager: UserManager
    ) -> None:
        self.database_manager = database_manager
        self.user_manager = user_manager

    def encrypt_file(
        self,
        input_path: str | Path,
        recipient_uuids: list[str],
        owner_uuid: str | None = None,
    ) -> EncryptionResult:
        """Encrypt a file for the given recipient UUIDs."""

        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not input_file.is_file():
            raise ValueError(f"Path is not a file: {input_file}")

        normalized_recipient_uuids = [
            recipient_uuid.strip()
            for recipient_uuid in recipient_uuids
            if recipient_uuid.strip()
        ]
        if owner_uuid:
            normalized_owner_uuid = owner_uuid.strip()
            if (
                normalized_owner_uuid
                and normalized_owner_uuid not in normalized_recipient_uuids
            ):
                normalized_recipient_uuids.insert(0, normalized_owner_uuid)
        if not normalized_recipient_uuids:
            raise ValueError("At least one recipient UUID is required.")

        aes_key = os.urandom(AES_KEY_SIZE)
        recipients = [
            self._build_recipient(recipient_uuid, aes_key)
            for recipient_uuid in normalized_recipient_uuids
        ]
        output_file = Path(f"{input_file}.pet")

        if output_file.exists():
            raise FileExistsError(f"Output file already exists: {output_file}")

        nonce = os.urandom(NONCE_SIZE)
        header = FileHeader(
            version=PET_VERSION,
            algorithm=ALGORITHM_AES_256_GCM,
            nonce=nonce,
            recipients=recipients,
        )
        header_bytes = self._serialize_header(header)

        plaintext = input_file.read_bytes()
        encrypted_payload = AESGCM(aes_key).encrypt(nonce, plaintext, header_bytes)
        ciphertext, auth_tag = (
            encrypted_payload[:-AUTH_TAG_SIZE],
            encrypted_payload[-AUTH_TAG_SIZE:],
        )

        with output_file.open("wb") as handle:
            handle.write(header_bytes)
            handle.write(ciphertext)
            handle.write(auth_tag)

        try:
            input_file.unlink()
        except OSError as error:
            output_file.unlink(missing_ok=True)
            raise OSError(
                f"Encrypted file was created, but the original file could not be deleted: {input_file}"
            ) from error

        return EncryptionResult(
            output_path=output_file, recipient_count=len(recipients)
        )

    def _build_recipient(self, recipient_uuid: str, aes_key: bytes) -> Recipient:
        user = self.user_manager.get_user_by_uuid(recipient_uuid)
        if user is None:
            raise ValueError(f"Unknown recipient UUID: {recipient_uuid}")

        record = self.database_manager.fetch_one(
            "SELECT public_key FROM users WHERE uuid = ?",
            (recipient_uuid,),
        )
        if record is None or not record["public_key"]:
            raise ValueError(f"Recipient has no public key: {recipient_uuid}")

        public_key_bytes = Base64Encoder.decode(record["public_key"])
        public_key = PublicKey(public_key_bytes)
        encrypted_aes_key = SealedBox(public_key).encrypt(aes_key)
        return Recipient(uuid=user.uuid, encrypted_aes_key=encrypted_aes_key)

    def _serialize_header(self, header: FileHeader) -> bytes:
        payload = bytearray()
        payload.extend(PET_MAGIC)
        payload.append(header.version)
        payload.append(header.algorithm)
        payload.extend(header.nonce)
        payload.extend(
            len(header.recipients).to_bytes(RECIPIENT_COUNT_SIZE, byteorder="big")
        )
        for recipient in header.recipients:
            recipient_uuid_bytes = recipient.uuid.encode("utf-8")
            if len(recipient_uuid_bytes) != UUID_LENGTH:
                raise ValueError(
                    f"Recipient UUID must be {UUID_LENGTH} characters: {recipient.uuid}"
                )
            payload.extend(recipient_uuid_bytes)
            payload.extend(
                len(recipient.encrypted_aes_key).to_bytes(
                    ENCRYPTED_KEY_LENGTH_SIZE, byteorder="big"
                )
            )
            payload.extend(recipient.encrypted_aes_key)
        return bytes(payload)
