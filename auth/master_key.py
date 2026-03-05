"""
Master password and encryption key management.
Single password system for personal use.
"""

import hashlib
import os
import json
from typing import Optional


class MasterKeyManager:
    """Manages master password and derives encryption keys."""

    def __init__(self, config_file: str = "pet_master.json"):
        """Initialize master key manager."""
        self.config_file = config_file
        self.master_key: Optional[bytes] = None

    def _derive_key(self, password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Master password
            salt: Random salt bytes
            iterations: Number of iterations for PBKDF2

        Returns:
            32-byte encryption key
        """
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)

    def is_initialized(self) -> bool:
        """Check if master password has been set up."""
        return os.path.exists(self.config_file)

    def initialize(self, password: str) -> bool:
        """
        Set up master password for first time.

        Args:
            password: Master password to set

        Returns:
            True if successful
        """
        if self.is_initialized():
            return False

        # Generate random salt
        salt = os.urandom(32)

        # Derive key and create verification hash
        key = self._derive_key(password, salt)
        verification_hash = hashlib.sha256(key).hexdigest()

        # Store salt and verification hash
        config: dict[str, str | int] = {
            'salt': salt.hex(),
            'verification_hash': verification_hash,
            'iterations': 100000
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        # Set file permissions (Windows)
        try:
            import stat
            os.chmod(self.config_file, stat.S_IRUSR | stat.S_IWUSR)  # Read/write for owner only
        except (OSError, AttributeError):
            pass  # Permissions not critical since content is hashed

        self.master_key = key
        return True

    def unlock(self, password: str) -> bool:
        """
        Verify master password and derive encryption key.

        Args:
            password: Master password to verify

        Returns:
            True if password correct and key derived
        """
        if not self.is_initialized():
            return False

        # Load configuration
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        salt = bytes.fromhex(config['salt'])
        stored_hash = config['verification_hash']
        iterations = config.get('iterations', 100000)

        # Derive key from password
        key = self._derive_key(password, salt, iterations)

        # Verify by comparing hash
        verification_hash = hashlib.sha256(key).hexdigest()

        if verification_hash == stored_hash:
            self.master_key = key
            return True

        return False

    def get_encryption_key(self) -> Optional[bytes]:
        """
        Get the derived encryption key.

        Returns:
            32-byte encryption key if unlocked, None otherwise
        """
        return self.master_key

    def is_unlocked(self) -> bool:
        """Check if master key is currently available."""
        return self.master_key is not None

    def lock(self):
        """Clear the master key from memory."""
        if self.master_key:
            # Overwrite key in memory before deleting
            self.master_key = b'\x00' * len(self.master_key)
            self.master_key = None

    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        Change the master password.

        Args:
            old_password: Current master password
            new_password: New master password to set

        Returns:
            True if password changed successfully
        """
        # Verify old password
        if not self.unlock(old_password):
            return False

        # Generate new salt and derive new key
        salt = os.urandom(32)
        key = self._derive_key(new_password, salt)
        verification_hash = hashlib.sha256(key).hexdigest()

        # Update configuration
        config: dict[str, str | int] = {
            'salt': salt.hex(),
            'verification_hash': verification_hash,
            'iterations': 100000
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        self.master_key = key
        return True
