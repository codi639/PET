"""Windows Credential Manager access for PET."""

from __future__ import annotations

import keyring
from keyring.errors import PasswordDeleteError


class CredentialManager:
    """Store and remove private keys in Windows Credential Manager."""

    def credential_name(self, user_uuid: str) -> str:
        """Return the service name used to store a user's private key."""

        return f"PET_PRIVATE_{user_uuid}"

    def store_private_key(self, user_uuid: str, private_key: str) -> None:
        """Store a private key for a user UUID."""

        keyring.set_password(self.credential_name(user_uuid), user_uuid, private_key)

    def get_private_key(self, user_uuid: str) -> str | None:
        """Retrieve a stored private key for a user UUID."""

        return keyring.get_password(self.credential_name(user_uuid), user_uuid)

    def delete_private_key(self, user_uuid: str) -> None:
        """Delete a stored private key if one exists."""

        try:
            keyring.delete_password(self.credential_name(user_uuid), user_uuid)
        except PasswordDeleteError:
            pass
