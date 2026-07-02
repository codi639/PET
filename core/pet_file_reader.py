"""PET file reader for the hybrid encryption engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.encryption_manager import (
    ALGORITHM_AES_256_GCM,
    AUTH_TAG_SIZE,
    ENCRYPTED_KEY_LENGTH_SIZE,
    NONCE_SIZE,
    PET_MAGIC,
    PET_VERSION,
    RECIPIENT_COUNT_SIZE,
    UUID_LENGTH,
)


@dataclass(slots=True)
class ParsedRecipient:
    """Represent a single recipient entry from a PET file."""

    uuid: str
    encrypted_aes_key: bytes


@dataclass(slots=True)
class ParsedPETFile:
    """Represent the parsed PET file metadata and encrypted payload."""

    version: int
    algorithm: int
    nonce: bytes
    recipients: list[ParsedRecipient]
    header_bytes: bytes
    ciphertext: bytes
    auth_tag: bytes


class PETFileReader:
    """Read and validate PET hybrid-encrypted files."""

    def read(self, file_path: str | Path) -> ParsedPETFile:
        """Parse a PET file into header metadata and payload parts."""

        input_file = Path(file_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not input_file.is_file():
            raise ValueError(f"Path is not a file: {input_file}")

        data = input_file.read_bytes()
        minimum_size = (
            len(PET_MAGIC) + 1 + 1 + NONCE_SIZE + RECIPIENT_COUNT_SIZE + AUTH_TAG_SIZE
        )
        if len(data) < minimum_size:
            raise ValueError("File is too small to be a valid PET file.")

        offset = 0
        magic = data[offset : offset + len(PET_MAGIC)]
        offset += len(PET_MAGIC)
        if magic != PET_MAGIC:
            raise ValueError("Not a valid PET file.")

        version = data[offset]
        offset += 1
        if version != PET_VERSION:
            raise ValueError(f"Unsupported PET version: {version}")

        algorithm = data[offset]
        offset += 1
        if algorithm != ALGORITHM_AES_256_GCM:
            raise ValueError(f"Unsupported PET algorithm: {algorithm}")

        nonce = data[offset : offset + NONCE_SIZE]
        offset += NONCE_SIZE
        if len(nonce) != NONCE_SIZE:
            raise ValueError("Corrupted PET file: missing nonce.")

        recipient_count_bytes = data[offset : offset + RECIPIENT_COUNT_SIZE]
        offset += RECIPIENT_COUNT_SIZE
        if len(recipient_count_bytes) != RECIPIENT_COUNT_SIZE:
            raise ValueError("Corrupted PET file: missing recipient count.")
        recipient_count = int.from_bytes(recipient_count_bytes, byteorder="big")

        recipients: list[ParsedRecipient] = []
        for _ in range(recipient_count):
            recipient_uuid_bytes = data[offset : offset + UUID_LENGTH]
            offset += UUID_LENGTH
            if len(recipient_uuid_bytes) != UUID_LENGTH:
                raise ValueError("Corrupted PET file: incomplete recipient UUID.")
            recipient_uuid = recipient_uuid_bytes.decode("utf-8")

            encrypted_key_length_bytes = data[
                offset : offset + ENCRYPTED_KEY_LENGTH_SIZE
            ]
            offset += ENCRYPTED_KEY_LENGTH_SIZE
            if len(encrypted_key_length_bytes) != ENCRYPTED_KEY_LENGTH_SIZE:
                raise ValueError("Corrupted PET file: incomplete recipient key length.")
            encrypted_key_length = int.from_bytes(
                encrypted_key_length_bytes, byteorder="big"
            )

            encrypted_aes_key = data[offset : offset + encrypted_key_length]
            offset += encrypted_key_length
            if len(encrypted_aes_key) != encrypted_key_length:
                raise ValueError("Corrupted PET file: incomplete encrypted AES key.")

            recipients.append(
                ParsedRecipient(
                    uuid=recipient_uuid,
                    encrypted_aes_key=encrypted_aes_key,
                )
            )

        if len(data) < offset + AUTH_TAG_SIZE:
            raise ValueError("Corrupted PET file: missing ciphertext or auth tag.")

        header_bytes = data[:offset]
        ciphertext = data[offset:-AUTH_TAG_SIZE]
        auth_tag = data[-AUTH_TAG_SIZE:]

        return ParsedPETFile(
            version=version,
            algorithm=algorithm,
            nonce=nonce,
            recipients=recipients,
            header_bytes=header_bytes,
            ciphertext=ciphertext,
            auth_tag=auth_tag,
        )
