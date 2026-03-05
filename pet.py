"""
PET - Python Encryption Tool
Main entry point and CLI interface.
"""

import sys
import getpass
from auth.master_key import MasterKeyManager


def setup_master_password(key_mgr: MasterKeyManager) -> bool:
    """Set up master password on first run."""
    print("\n=== First Time Setup ===")
    print("Welcome to PET! Let's set up your master password.")
    print("This password will be used to encrypt/decrypt your files.\n")

    while True:
        password = getpass.getpass("Create master password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters for security.")
            continue

        password_confirm = getpass.getpass("Confirm master password: ")
        if password != password_confirm:
            print("Passwords do not match.")
            continue

        break

    if key_mgr.initialize(password):
        print("\nMaster password created successfully!")
        print("IMPORTANT: Keep this password safe. It cannot be recovered if lost.\n")
        return True
    else:
        print("\nFailed to initialize master password.")
        return False


def unlock_with_master_password(key_mgr: MasterKeyManager) -> bool:
    """Prompt user for master password to unlock."""
    print("\n=== PET - Python Encryption Tool ===")
    print("Enter your master password to continue\n")

    max_attempts = 3
    for attempt in range(max_attempts):
        password = getpass.getpass("Master password: ")

        if key_mgr.unlock(password):
            print("\nUnlocked successfully!")
            return True
        else:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                print(f"Invalid password. {remaining} attempt(s) remaining.\n")
            else:
                print("Invalid password. Access denied.")

    return False


def main_menu(key_mgr: MasterKeyManager):
    """Display and handle main menu."""
    while True:
        print("\n=== PET Main Menu ===")
        print("Unlocked")
        print()
        print("1. Encrypt file (Coming soon)")
        print("2. Decrypt file (Coming soon)")
        print("3. Change master password")
        print("0. Lock and exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            print("\nFile encryption feature coming soon!")
        elif choice == '2':
            print("\nFile decryption feature coming soon!")
        elif choice == '3':
            change_master_password(key_mgr)
        elif choice == '0':
            print("\nLocking... Goodbye!")
            key_mgr.lock()
            break
        else:
            print("✗ Invalid option.")


def change_master_password(key_mgr: MasterKeyManager):
    """Change the master password."""
    print("\n=== Change Master Password ===")

    old_password = getpass.getpass("Current master password: ")

    while True:
        new_password = getpass.getpass("New master password: ")
        if len(new_password) < 8:
            print("Password must be at least 8 characters.")
            continue

        confirm_password = getpass.getpass("Confirm new password: ")
        if new_password != confirm_password:
            print("Passwords do not match.")
            continue

        break

    if key_mgr.change_password(old_password, new_password):
        print("\nMaster password changed successfully!")
    else:
        print("\nFailed to change password. Current password may be incorrect.")


def main():
    """Main entry point for PET."""
    try:
        key_mgr = MasterKeyManager()

        # First time setup if not initialized
        if not key_mgr.is_initialized():
            if not setup_master_password(key_mgr):
                sys.exit(1)
        else:
            # Unlock with master password
            if not unlock_with_master_password(key_mgr):
                print("\nAuthentication failed. Exiting.")
                sys.exit(1)

        # Show main menu
        main_menu(key_mgr)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
        sys.exit(0)
    except (OSError, ValueError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
