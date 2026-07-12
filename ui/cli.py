"""Console interface for PET."""

from __future__ import annotations

from getpass import getpass
from pathlib import Path

from core.decryption_manager import DecryptionManager
from core.encryption_manager import EncryptionManager
from core.petkey_manager import PetKeyManager
from core.user_manager import UserManager
from models.user import User


def run_console(user_manager: UserManager) -> None:
    """Run the interactive console menu."""

    current_user: User | None = None

    while True:
        print()
        print("1 Create Account")
        print("2 Login")
        print("3 Show or Select Users")
        print("4 Encrypt File")
        print("5 Decrypt File")
        print("6 Change Password")
        print("7 Export Identity")
        print("8 Import Identity")
        print("9 Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            current_user = create_account(user_manager)
        elif choice == "2":
            current_user = login(user_manager)
        elif choice == "3":
            browse_users(user_manager)
        elif choice == "4":
            current_user = encrypt_file(user_manager, current_user)
        elif choice == "5":
            current_user = decrypt_file(user_manager, current_user)
        elif choice == "6":
            current_user = change_password(user_manager, current_user)
        elif choice == "7":
            current_user = export_identity(user_manager, current_user)
        elif choice == "8":
            current_user = import_identity(user_manager, current_user)
        elif choice == "9":
            print("Goodbye.")
            return
        else:
            print("Invalid option.")


def show_users(user_manager: UserManager) -> None:
    """Display every user with their UUID."""

    users = user_manager.retrieve_users()
    if not users:
        print("No users found.")
        return

    print("Users:")
    for user in users:
        print(f"- {user.username}: {user.uuid}")


def browse_users(user_manager: UserManager) -> None:
    """Prompt for usernames and show their UUIDs, or list all users when blank."""

    selected_users = prompt_recipient_users(
        user_manager,
        blank_mode="list_all",
    )
    if selected_users is None:
        return

    print("Selected users:")
    for user in selected_users:
        print(f"- {user.username}: {user.uuid}")


def prompt_recipient_users(
    user_manager: UserManager,
    *,
    blank_mode: str,
) -> list[User] | None:
    """Prompt for usernames and return matching users."""

    while True:
        recipient_input = input(
            "Usernames (comma-separated, leave blank for connected user only): "
        ).strip()
        if not recipient_input:
            if blank_mode == "list_all":
                show_users(user_manager)
                return None
            return []

        recipient_usernames = [
            recipient.strip()
            for recipient in recipient_input.split(",")
            if recipient.strip()
        ]
        if not recipient_usernames:
            print("Please enter at least one username.")
            continue

        users_by_username = {
            user.username: user for user in user_manager.retrieve_users()
        }
        selected_users: list[User] = []
        missing_usernames: list[str] = []

        for username in recipient_usernames:
            user = users_by_username.get(username)
            if user is None:
                missing_usernames.append(username)
                continue
            if all(existing_user.uuid != user.uuid for existing_user in selected_users):
                selected_users.append(user)

        if missing_usernames:
            print("Unknown usernames: " + ", ".join(missing_usernames))
            continue

        return selected_users


def encrypt_file(user_manager: UserManager, current_user: User | None) -> User | None:
    """Prompt for a file and recipient usernames, then encrypt the file."""

    if current_user is None:
        print("Authentication required.")
        current_user = login(user_manager)
        if current_user is None:
            return None

    input_path = input("File path: ").strip()
    selected_users = prompt_recipient_users(
        user_manager,
        blank_mode="self_only",
    )
    if selected_users is None:
        return current_user

    recipient_uuids = [user.uuid for user in selected_users]
    if current_user.uuid not in recipient_uuids:
        recipient_uuids.insert(0, current_user.uuid)

    encryption_manager = EncryptionManager(user_manager.database_manager, user_manager)
    try:
        result = encryption_manager.encrypt_file(
            Path(input_path),
            recipient_uuids,
            owner_uuid=current_user.uuid,
        )
    except Exception as error:
        print(error)
        return current_user

    print(f"Encrypted file created: {result.output_path}")
    return current_user


def decrypt_file(user_manager: UserManager, current_user: User | None) -> User | None:
    """Prompt for a PET file and decrypt it for the connected user."""

    if current_user is None:
        print("Authentication required.")
        current_user = login(user_manager)
        if current_user is None:
            return None

    input_path = input("PET file path: ").strip()
    decryption_manager = DecryptionManager(user_manager)
    try:
        result = decryption_manager.decrypt_file(Path(input_path), current_user.uuid)
    except Exception as error:
        print(error)
        return current_user

    print(f"Decrypted file created: {result.output_path}")
    return current_user


def change_password(
    user_manager: UserManager, current_user: User | None
) -> User | None:
    """Prompt the connected user to change their password."""

    if current_user is None:
        print("Authentication required.")
        current_user = login(user_manager)
        if current_user is None:
            return None

    current_password = getpass("Current password: ")
    new_password = getpass("New password: ")
    confirm_password = getpass("Confirm new password: ")

    if new_password != confirm_password:
        print("Passwords do not match.")
        return current_user

    try:
        updated_user = user_manager.change_password(
            current_user.uuid,
            current_password,
            new_password,
        )
    except ValueError as error:
        print(error)
        return current_user

    print(f"Password updated for {updated_user.username}.")
    return current_user


def export_identity(
    user_manager: UserManager, current_user: User | None
) -> User | None:
    """Export the connected user's identity to an encrypted .petkey file."""

    if current_user is None:
        print("Authentication required.")
        current_user = login(user_manager)
        if current_user is None:
            return None

    output_path = input("Export path (.petkey, optional): ").strip()
    export_passphrase = getpass("Export passphrase: ")
    confirm_passphrase = getpass("Confirm export passphrase: ")
    if export_passphrase != confirm_passphrase:
        print("Passphrases do not match.")
        return current_user

    petkey_manager = PetKeyManager(user_manager)
    try:
        result_path = petkey_manager.export_identity(
            current_user.uuid,
            output_path or None,
            export_passphrase,
        )
    except Exception as error:
        print(error)
        return current_user

    print(f"Identity exported: {result_path}")
    return current_user


def import_identity(
    user_manager: UserManager, current_user: User | None
) -> User | None:
    """Import a .petkey identity and create or update the local user."""

    input_path = input("PETKEY file path: ").strip()
    export_passphrase = getpass("Export passphrase: ")
    user_password = getpass("User password: ")
    confirm_password = getpass("Confirm user password: ")
    if user_password != confirm_password:
        print("Passwords do not match.")
        return current_user

    petkey_manager = PetKeyManager(user_manager)
    try:
        user = petkey_manager.import_identity(
            Path(input_path),
            export_passphrase,
            user_password,
        )
    except Exception as error:
        print(error)
        return current_user

    print(f"Identity imported successfully: {user.username} ({user.uuid})")
    return user


def create_account(user_manager: UserManager) -> User | None:
    """Prompt for account details and create a new user."""

    username = input("Username: ").strip()
    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    try:
        result = user_manager.create_account(username, password)
    except ValueError as error:
        print(error)
        return None

    print("User created successfully")
    print(result.user.uuid)
    print(result.public_key_fingerprint)
    return result.user


def login(user_manager: UserManager) -> User | None:
    """Prompt for credentials and log the user in."""

    username = input("Username: ").strip()
    password = getpass("Password: ")

    try:
        user = user_manager.login(username, password)
    except ValueError as error:
        print(error)
        return None

    print(f"Welcome back, {user.username}.")
    return user
