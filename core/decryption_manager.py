"""PET file decryption engine for PET."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from nacl.encoding import Base64Encoder
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, SealedBox

from core.credential_manager import CredentialManager
from core.user_manager import UserManager
from core.pet_file_reader import PETFileReader


@dataclass(slots=True)
class DecryptionResult:
    """Return value for a successful decryption operation."""

    output_path: Path


class DecryptionManager:
    """Recover the AES key for the current user and decrypt PET files."""

    def __init__(self, user_manager: UserManager) -> None:
        self.user_manager = user_manager
        self.pet_file_reader = PETFileReader()
        self.credential_manager = CredentialManager()

    def decrypt_file(self, input_path: str | Path, user_uuid: str) -> DecryptionResult:
        """Decrypt a PET file for the provided user UUID."""

        parsed_file = self.pet_file_reader.read(input_path)
        recipient = next(
            (entry for entry in parsed_file.recipients if entry.uuid == user_uuid),
            None,
        )
        if recipient is None:
            raise PermissionError("This file is not encrypted for the connected user.")

        user = self.user_manager.get_user_by_uuid(user_uuid)
        if user is None:
            raise PermissionError("Unknown user.")

        private_key_b64 = self.credential_manager.get_private_key(user_uuid)
        if private_key_b64 is None:
            raise PermissionError("Private key not available for this user.")

        try:
            private_key = PrivateKey(Base64Encoder.decode(private_key_b64))
            aes_key = SealedBox(private_key).decrypt(recipient.encrypted_aes_key)
            plaintext = AESGCM(aes_key).decrypt(
                parsed_file.nonce,
                parsed_file.ciphertext + parsed_file.auth_tag,
                parsed_file.header_bytes,
            )
        except (CryptoError, InvalidTag, ValueError):
            raise PermissionError("Unable to decrypt this PET file.") from None

        input_file = Path(input_path)
        output_file = self._restore_original_path(input_file)
        if output_file.exists():
            raise FileExistsError(f"Output file already exists: {output_file}")

        output_file.write_bytes(plaintext)
        return DecryptionResult(output_path=output_file)

    def _restore_original_path(self, input_file: Path) -> Path:
        """Restore the original filename by removing the final .pet suffix."""

        if input_file.suffix.lower() == ".pet":
            return Path(str(input_file)[:-4])
        return input_file.with_suffix("")
