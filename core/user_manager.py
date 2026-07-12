"""User management for PET."""

from __future__ import annotations

from datetime import datetime, timezone

from core.credential_manager import CredentialManager
from core.database import DatabaseManager
from core.key_manager import KeyManager
from core.password_manager import PasswordManager
from models.identity import AccountCreationResult
from models.user import User


class UserManager:
    """Create accounts, log in users, and retrieve user records."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager = database_manager
        self.password_manager = PasswordManager()
        self.key_manager = KeyManager()
        self.credential_manager = CredentialManager()

    def create_account(self, username: str, password: str) -> AccountCreationResult:
        """Create a new account and return the created user details."""

        normalized_username = username.strip()
        if not normalized_username:
            raise ValueError("Username cannot be empty.")
        if not password:
            raise ValueError("Password cannot be empty.")
        if self.username_exists(normalized_username):
            raise ValueError("Username already exists.")

        generated_identity = self.key_manager.generate_key_pair()
        password_hash = self.password_manager.hash_password(password)
        private_key_encoded = self.key_manager.encode_private_key(
            generated_identity.private_key
        )
        public_key_encoded = self.key_manager.encode_public_key(
            generated_identity.public_key
        )

        self.credential_manager.store_private_key(
            generated_identity.uuid,
            private_key_encoded,
        )

        created_at = datetime.now(timezone.utc).isoformat()
        try:
            self.database_manager.execute(
                """
                INSERT INTO users (uuid, username, password_hash, public_key, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    generated_identity.uuid,
                    normalized_username,
                    password_hash,
                    public_key_encoded,
                    created_at,
                ),
            )
        except Exception:
            self.credential_manager.delete_private_key(generated_identity.uuid)
            raise

        user = self.get_user_by_username(normalized_username)
        if user is None:
            self.credential_manager.delete_private_key(generated_identity.uuid)
            raise RuntimeError("User was created but could not be reloaded.")

        fingerprint = self.key_manager.public_key_fingerprint(
            generated_identity.public_key
        )
        return AccountCreationResult(user=user, public_key_fingerprint=fingerprint)

    def login(self, username: str, password: str) -> User:
        """Verify credentials and return the matching user."""

        record = self.database_manager.fetch_one(
            """
            SELECT id, uuid, username, password_hash, created_at
            FROM users
            WHERE username = ?
            """,
            (username.strip(),),
        )
        if record is None:
            raise ValueError("Invalid username or password.")

        if not self.password_manager.verify_password(password, record["password_hash"]):
            raise ValueError("Invalid username or password.")

        return User(
            id=record["id"],
            uuid=record["uuid"],
            username=record["username"],
            created_at=record["created_at"],
        )

    def change_password(
        self,
        user_uuid: str,
        current_password: str,
        new_password: str,
    ) -> User:
        """Change a user's password without changing their UUID or keys."""

        record = self.database_manager.fetch_one(
            """
            SELECT id, uuid, username, password_hash, created_at
            FROM users
            WHERE uuid = ?
            """,
            (user_uuid,),
        )
        if record is None:
            raise ValueError("Unknown user.")

        if not self.password_manager.verify_password(
            current_password, record["password_hash"]
        ):
            raise ValueError("Invalid current password.")

        normalized_new_password = new_password.strip()
        if not normalized_new_password:
            raise ValueError("New password cannot be empty.")

        new_password_hash = self.password_manager.hash_password(normalized_new_password)
        self.database_manager.execute(
            "UPDATE users SET password_hash = ? WHERE uuid = ?",
            (new_password_hash, user_uuid),
        )

        return User(
            id=record["id"],
            uuid=record["uuid"],
            username=record["username"],
            created_at=record["created_at"],
        )

    def import_user_identity(
        self,
        username: str,
        user_uuid: str,
        public_key: str,
        private_key: str,
        password: str,
        created_at: str,
    ) -> User:
        """Import a user identity while keeping the UUID and keys stable."""

        normalized_username = username.strip()
        normalized_uuid = user_uuid.strip()
        normalized_public_key = public_key.strip()
        normalized_private_key = private_key.strip()
        normalized_created_at = (
            created_at.strip() or datetime.now(timezone.utc).isoformat()
        )

        if not normalized_username:
            raise ValueError("Username cannot be empty.")
        if not normalized_uuid:
            raise ValueError("UUID cannot be empty.")
        if not normalized_public_key:
            raise ValueError("Public key cannot be empty.")
        if not normalized_private_key:
            raise ValueError("Private key cannot be empty.")
        if not password:
            raise ValueError("Password cannot be empty.")

        existing_by_uuid = self.database_manager.fetch_one(
            """
            SELECT id, uuid, username, password_hash, public_key, created_at
            FROM users
            WHERE uuid = ?
            """,
            (normalized_uuid,),
        )
        conflicting_username = self.get_user_by_username(normalized_username)
        if (
            conflicting_username is not None
            and conflicting_username.uuid != normalized_uuid
        ):
            raise ValueError("Username already exists.")

        password_hash = self.password_manager.hash_password(password)

        if existing_by_uuid is None:
            try:
                self.database_manager.execute(
                    """
                    INSERT INTO users (uuid, username, password_hash, public_key, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_uuid,
                        normalized_username,
                        password_hash,
                        normalized_public_key,
                        normalized_created_at,
                    ),
                )
                self.credential_manager.store_private_key_verified(
                    normalized_uuid,
                    normalized_private_key,
                )
            except Exception:
                self.database_manager.execute(
                    "DELETE FROM users WHERE uuid = ?",
                    (normalized_uuid,),
                )
                self.credential_manager.delete_private_key(normalized_uuid)
                raise
        else:
            try:
                self.database_manager.execute(
                    """
                    UPDATE users
                    SET username = ?, password_hash = ?, public_key = ?, created_at = ?
                    WHERE uuid = ?
                    """,
                    (
                        normalized_username,
                        password_hash,
                        normalized_public_key,
                        normalized_created_at,
                        normalized_uuid,
                    ),
                )
                self.credential_manager.store_private_key_verified(
                    normalized_uuid,
                    normalized_private_key,
                )
            except Exception:
                self.database_manager.execute(
                    """
                    UPDATE users
                    SET username = ?, password_hash = ?, public_key = ?, created_at = ?
                    WHERE uuid = ?
                    """,
                    (
                        existing_by_uuid["username"],
                        existing_by_uuid["password_hash"],
                        existing_by_uuid["public_key"],
                        existing_by_uuid["created_at"],
                        normalized_uuid,
                    ),
                )
                self.credential_manager.delete_private_key(normalized_uuid)
                raise

        user = self.get_user_by_uuid(normalized_uuid)
        if user is None:
            raise RuntimeError("User was imported but could not be reloaded.")

        return user

    def username_exists(self, username: str) -> bool:
        """Return True when a username already exists."""

        record = self.database_manager.fetch_one(
            "SELECT 1 FROM users WHERE username = ?",
            (username.strip(),),
        )
        return record is not None

    def get_user_by_username(self, username: str) -> User | None:
        """Retrieve one user by username."""

        return self.database_manager.fetch_one(
            """
            SELECT id, uuid, username, created_at
            FROM users
            WHERE username = ?
            """,
            (username.strip(),),
            mapper=lambda row: User(
                id=row["id"],
                uuid=row["uuid"],
                username=row["username"],
                created_at=row["created_at"],
            ),
        )

    def get_user_by_uuid(self, user_uuid: str) -> User | None:
        """Retrieve one user by UUID."""

        return self.database_manager.fetch_one(
            """
            SELECT id, uuid, username, created_at
            FROM users
            WHERE uuid = ?
            """,
            (user_uuid,),
            mapper=lambda row: User(
                id=row["id"],
                uuid=row["uuid"],
                username=row["username"],
                created_at=row["created_at"],
            ),
        )

    def retrieve_users(self) -> list[User]:
        """Return all users stored in the database."""

        return self.database_manager.fetch_all(
            """
            SELECT id, uuid, username, created_at
            FROM users
            ORDER BY id ASC
            """,
            mapper=lambda row: User(
                id=row["id"],
                uuid=row["uuid"],
                username=row["username"],
                created_at=row["created_at"],
            ),
        )
