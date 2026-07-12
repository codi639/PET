"""PET identity export and import using encrypted .petkey files."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.credential_manager import CredentialManager
from core.user_manager import UserManager
from models.user import User

PETKEY_MAGIC = b"PETKEY\xae\x42"
PETKEY_VERSION = 1
SALT_SIZE = 16
NONCE_SIZE = 12
DERIVED_KEY_SIZE = 32
TIME_COST = 3
MEMORY_COST = 64 * 1024
PARALLELISM = 4


@dataclass(slots=True)
class PetKeyPayload:
    """Identity payload stored inside a .petkey file."""

    schema_version: int
    username: str
    uuid: str
    public_key: str
    private_key: str
    created_at: str


@dataclass(slots=True)
class ParsedPetKeyFile:
    """Parsed PETKEY file header and encrypted payload."""

    salt: bytes
    nonce: bytes
    time_cost: int
    memory_cost: int
    parallelism: int
    header_bytes: bytes
    encrypted_payload: bytes


class PetKeyManager:
    """Export and import PET identities as encrypted .petkey files."""

    def __init__(self, user_manager: UserManager) -> None:
        self.user_manager = user_manager
        self.credential_manager = CredentialManager()

    def export_identity(
        self,
        user_uuid: str,
        output_path: str | Path | None,
        passphrase: str,
    ) -> Path:
        """Export a user identity to an encrypted .petkey file."""

        user = self.user_manager.get_user_by_uuid(user_uuid)
        if user is None:
            raise ValueError("Unknown user.")

        record = self.user_manager.database_manager.fetch_one(
            "SELECT public_key FROM users WHERE uuid = ?",
            (user_uuid,),
        )
        if record is None or not record["public_key"]:
            raise ValueError("Public key not found for this user.")

        private_key = self.credential_manager.get_private_key(user_uuid)
        if private_key is None:
            raise ValueError("Private key not found for this user.")

        payload = PetKeyPayload(
            schema_version=1,
            username=user.username,
            uuid=user.uuid,
            public_key=record["public_key"],
            private_key=private_key,
            created_at=user.created_at,
        )
        payload_bytes = json.dumps(asdict(payload), sort_keys=True).encode("utf-8")

        salt = os.urandom(SALT_SIZE)
        nonce = os.urandom(NONCE_SIZE)
        header_bytes = self._serialize_header(salt, nonce)
        derived_key = self._derive_key(
            passphrase, salt, TIME_COST, MEMORY_COST, PARALLELISM
        )
        encrypted_payload = AESGCM(derived_key).encrypt(
            nonce, payload_bytes, header_bytes
        )

        output_file = self._resolve_output_path(output_path, user.username)
        if output_file.exists():
            raise FileExistsError(f"Output file already exists: {output_file}")

        output_file.write_bytes(header_bytes + encrypted_payload)
        return output_file

    def import_identity(
        self,
        input_path: str | Path,
        passphrase: str,
        password: str,
    ) -> User:
        """Import a PET identity from an encrypted .petkey file."""

        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not input_file.is_file():
            raise ValueError(f"Path is not a file: {input_file}")

        parsed_file = self._parse_file(input_file)
        derived_key = self._derive_key(
            passphrase,
            parsed_file.salt,
            parsed_file.time_cost,
            parsed_file.memory_cost,
            parsed_file.parallelism,
        )

        try:
            payload_bytes = AESGCM(derived_key).decrypt(
                parsed_file.nonce,
                parsed_file.encrypted_payload,
                parsed_file.header_bytes,
            )
        except (InvalidTag, ValueError):
            raise PermissionError("Unable to open the .petkey file.") from None

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            raise PermissionError("Unable to open the .petkey file.") from None

        required_fields = {
            "schema_version",
            "username",
            "uuid",
            "public_key",
            "private_key",
            "created_at",
        }
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise PermissionError("Unable to open the .petkey file.")
        if not required_fields.issubset(payload):
            raise PermissionError("Unable to open the .petkey file.")

        return self.user_manager.import_user_identity(
            username=payload["username"],
            user_uuid=payload["uuid"],
            public_key=payload["public_key"],
            private_key=payload["private_key"],
            password=password,
            created_at=payload.get("created_at", ""),
        )

    def _derive_key(
        self,
        passphrase: str,
        salt: bytes,
        time_cost: int,
        memory_cost: int,
        parallelism: int,
    ) -> bytes:
        return hash_secret_raw(
            secret=passphrase.encode("utf-8"),
            salt=salt,
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=DERIVED_KEY_SIZE,
            type=Type.ID,
        )

    def _serialize_header(self, salt: bytes, nonce: bytes) -> bytes:
        header = bytearray()
        header.extend(PETKEY_MAGIC)
        header.append(PETKEY_VERSION)
        header.extend(salt)
        header.extend(nonce)
        header.extend(TIME_COST.to_bytes(4, byteorder="big"))
        header.extend(MEMORY_COST.to_bytes(4, byteorder="big"))
        header.extend(PARALLELISM.to_bytes(1, byteorder="big"))
        return bytes(header)

    def _parse_file(self, input_file: Path) -> ParsedPetKeyFile:
        data = input_file.read_bytes()
        minimum_size = len(PETKEY_MAGIC) + 1 + SALT_SIZE + NONCE_SIZE + 4 + 4 + 1
        if len(data) < minimum_size:
            raise ValueError("File is too small to be a valid .petkey file.")

        offset = 0
        magic = data[offset : offset + len(PETKEY_MAGIC)]
        offset += len(PETKEY_MAGIC)
        if magic != PETKEY_MAGIC:
            raise ValueError("Not a valid .petkey file.")

        version = data[offset]
        offset += 1
        if version != PETKEY_VERSION:
            raise ValueError(f"Unsupported .petkey version: {version}")

        salt = data[offset : offset + SALT_SIZE]
        offset += SALT_SIZE
        if len(salt) != SALT_SIZE:
            raise ValueError("Corrupted .petkey file: missing salt.")

        nonce = data[offset : offset + NONCE_SIZE]
        offset += NONCE_SIZE
        if len(nonce) != NONCE_SIZE:
            raise ValueError("Corrupted .petkey file: missing nonce.")

        time_cost = int.from_bytes(data[offset : offset + 4], byteorder="big")
        offset += 4
        memory_cost = int.from_bytes(data[offset : offset + 4], byteorder="big")
        offset += 4
        parallelism = data[offset]
        offset += 1

        header_bytes = data[:offset]
        encrypted_payload = data[offset:]
        if not encrypted_payload:
            raise ValueError("Corrupted .petkey file: missing encrypted payload.")

        return ParsedPetKeyFile(
            salt=salt,
            nonce=nonce,
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            header_bytes=header_bytes,
            encrypted_payload=encrypted_payload,
        )

    def _resolve_output_path(
        self,
        output_path: str | Path | None,
        username: str,
    ) -> Path:
        default_name = f"{username}.petkey"
        if output_path is None:
            return Path(default_name)

        resolved_path = Path(output_path)
        if not str(resolved_path):
            return Path(default_name)
        if resolved_path.is_dir():
            return resolved_path / default_name
        if resolved_path.suffix.lower() != ".petkey":
            return resolved_path.with_suffix(".petkey")
        return resolved_path
