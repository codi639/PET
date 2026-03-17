"""
PET - Personal Encryption Tool
Command Line Interface implementation.
"""

import sys
import argparse
import getpass
from pathlib import Path
from auth.master_key import MasterKeyManager
from encryption import encrypt_file, decrypt_file, PET_EXTENSION
from encryption.file_crypto import EncryptionError, DecryptionError


def encrypt_file_non_interactive(key_mgr: MasterKeyManager, input_path: str, output_path: str | None = None, delete_original: bool = False) -> bool:
    """
    Encrypt a file without user interaction.
    
    Args:
        key_mgr: Master key manager instance
        input_path: Path to file to encrypt
        output_path: Optional output path. If None, uses input_path + .pet
        delete_original: Whether to delete original file after encryption
        
    Returns:
        True if successful, False otherwise
    """
    # Remove quotes if present
    input_path = input_path.strip('"').strip("'")
    
    # Check if file exists
    if not Path(input_path).exists():
        print(f"Error: File not found: {input_path}")
        return False
    
    # Check if it's already encrypted
    if input_path.lower().endswith(PET_EXTENSION):
        print(f"Error: File is already encrypted (has {PET_EXTENSION} extension).")
        return False
    
    # Determine output path
    if output_path is None:
        output_path = input_path + PET_EXTENSION
    else:
        output_path = output_path.strip('"').strip("'")
    
    # Check if output already exists
    if Path(output_path).exists():
        print(f"Error: Output file already exists: {output_path}")
        return False
    
    # Get encryption key
    encryption_key = key_mgr.get_encryption_key()
    if not encryption_key:
        print("Error: Encryption key not available. Please unlock first.")
        return False
    
    try:
        encrypt_file(input_path, output_path, encryption_key)
        print(f"Success: File encrypted: {output_path}")
        
        if delete_original:
            try:
                Path(input_path).unlink()
                print("Success: Original file deleted")
            except OSError as e:
                print(f"Warning: Could not delete original file: {e}")
        
        return True
        
    except (EncryptionError, FileNotFoundError, OSError, ValueError) as e:
        print(f"Error: Encryption failed: {e}")
        return False


def decrypt_file_non_interactive(key_mgr: MasterKeyManager, input_path: str, output_path: str | None = None, delete_original: bool = False, overwrite: bool = False) -> bool:
    """
    Decrypt a file without user interaction.
    
    Args:
        key_mgr: Master key manager instance
        input_path: Path to encrypted file
        output_path: Optional output path. If None, removes .pet extension
        delete_original: Whether to delete encrypted file after decryption
        overwrite: Whether to overwrite existing output file
        
    Returns:
        True if successful, False otherwise
    """
    # Remove quotes if present
    input_path = input_path.strip('"').strip("'")
    
    # Check if file exists
    if not Path(input_path).exists():
        print(f"Error: File not found: {input_path}")
        return False
    
    # Determine output path
    if output_path is None:
        if input_path.lower().endswith(PET_EXTENSION):
            output_path = input_path[:-len(PET_EXTENSION)]
        else:
            output_path = input_path + ".decrypted"
    else:
        output_path = output_path.strip('"').strip("'")
    
    # Check if output already exists
    if Path(output_path).exists() and not overwrite:
        print(f"Error: Output file already exists: {output_path}")
        return False
    
    # Delete existing file if overwrite is True
    if Path(output_path).exists() and overwrite:
        try:
            Path(output_path).unlink()
        except OSError as e:
            print(f"Error: Could not delete existing file: {e}")
            return False
    
    # Get encryption key
    encryption_key = key_mgr.get_encryption_key()
    if not encryption_key:
        print("Error: Encryption key not available. Please unlock first.")
        return False
    
    try:
        decrypt_file(input_path, output_path, encryption_key, overwrite=overwrite)
        print(f"Success: File decrypted: {output_path}")
        
        if delete_original:
            try:
                Path(input_path).unlink()
                print("Success: Encrypted file deleted")
            except OSError as e:
                print(f"Warning: Could not delete encrypted file: {e}")
        
        return True
        
    except (DecryptionError, FileNotFoundError, OSError, ValueError) as e:
        print(f"Error: Decryption failed: {e}")
        return False


def setup_master_password_cli(key_mgr: MasterKeyManager) -> bool:
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


def unlock_with_master_password_cli(key_mgr: MasterKeyManager) -> bool:
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


def main_menu_cli(key_mgr: MasterKeyManager):
    """Display and handle main menu."""
    while True:
        print("\n=== PET Main Menu ===")
        print("Unlocked")
        print()
        print("1. Encrypt file")
        print("2. Decrypt file")
        print("3. Change master password")
        print("0. Lock and exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            encrypt_file_cli(key_mgr)
        elif choice == '2':
            decrypt_file_cli(key_mgr)
        elif choice == '3':
            change_master_password_cli(key_mgr)
        elif choice == '0':
            print("\nLocking... Goodbye!")
            key_mgr.lock()
            break
        else:
            print("Invalid option.")


def encrypt_file_cli(key_mgr: MasterKeyManager) -> None:
    """Handle file encryption in CLI."""
    print("\n=== Encrypt File ===")

    # Get input file path
    input_path = input("Enter path to file to encrypt: ").strip()
    if not input_path:
        print("No file path provided.")
        return

    # Remove quotes if user copied path with quotes
    input_path = input_path.strip('"').strip("'")

    # Check if file exists
    if not Path(input_path).exists():
        print(f"File not found: {input_path}")
        return

    # Check if it's already a .pet file
    if input_path.lower().endswith(PET_EXTENSION):
        print(f"File is already encrypted (has {PET_EXTENSION} extension).")
        return

    # Get output path (optional)
    output_path = input(f"Output path (press Enter for '{input_path}{PET_EXTENSION}'): ").strip()
    if not output_path:
        output_path = None
    else:
        output_path = output_path.strip('"').strip("'")

    # Get encryption key
    encryption_key = key_mgr.get_encryption_key()
    if not encryption_key:
        print("Encryption key not available. Please unlock first.")
        return

    try:
        print("\nEncrypting file...")
        result_path = encrypt_file(input_path, output_path, encryption_key)
        print("File encrypted successfully!")
        print(f"  Encrypted file: {result_path}")

        # Ask if user wants to delete original
        delete = input("\nDelete original file? (yes/no): ").strip().lower()
        if delete in ('yes', 'y'):
            try:
                Path(input_path).unlink()
                print("Original file deleted.")
            except OSError as e:
                print(f"Failed to delete original file: {e}")

    except EncryptionError as e:
        print(f"Encryption failed: {e}")
    except (OSError, ValueError) as e:
        print(f"Unexpected error: {e}")


def decrypt_file_cli(key_mgr: MasterKeyManager) -> None:
    """Handle file decryption in CLI."""
    print("\n=== Decrypt File ===")

    # Get input file path
    input_path = input("Enter path to encrypted file: ").strip()
    if not input_path:
        print("No file path provided.")
        return

    # Remove quotes if user copied path with quotes
    input_path = input_path.strip('"').strip("'")

    # Check if file exists
    if not Path(input_path).exists():
        print(f"File not found: {input_path}")
        return

    # Warn if not a .pet file
    if not input_path.lower().endswith(PET_EXTENSION):
        print(f"Warning: File does not have {PET_EXTENSION} extension.")
        proceed = input("Continue anyway? (yes/no): ").strip().lower()
        if proceed not in ('yes', 'y'):
            print("Decryption cancelled.")
            return

    # Get output path (optional)
    default_output = input_path[:-len(PET_EXTENSION)] if input_path.lower().endswith(PET_EXTENSION) else input_path + ".decrypted"
    output_path = input(f"Output path (press Enter for '{default_output}'): ").strip()
    if not output_path:
        output_path = None
    else:
        output_path = output_path.strip('"').strip("'")

    # Check if output exists
    check_path = Path(output_path) if output_path else Path(default_output)
    overwrite = False
    if check_path.exists():
        overwrite_input = input(f"⚠ Output file '{check_path}' already exists. Overwrite? (yes/no): ").strip().lower()
        if overwrite_input not in ('yes', 'y'):
            print("Decryption cancelled.")
            return
        overwrite = True

    # Get encryption key
    encryption_key = key_mgr.get_encryption_key()
    if not encryption_key:
        print("Encryption key not available. Please unlock first.")
        return

    try:
        print("\nDecrypting file...")
        result_path = decrypt_file(input_path, output_path, encryption_key, overwrite=overwrite)
        print("File decrypted successfully!")
        print(f"  Decrypted file: {result_path}")

        # Ask if user wants to delete encrypted file
        delete = input("\nDelete encrypted file? (yes/no): ").strip().lower()
        if delete in ('yes', 'y'):
            try:
                Path(input_path).unlink()
                print("Encrypted file deleted.")
            except OSError as e:
                print(f"Failed to delete encrypted file: {e}")

    except DecryptionError as e:
        print(f"Decryption failed: {e}")
    except (OSError, ValueError) as e:
        print(f"Unexpected error: {e}")


def change_master_password_cli(key_mgr: MasterKeyManager):
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


def run_cli():
    """Main entry point for CLI interface."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="PET - Python Encryption Tool",
        prog="pet"
    )
    parser.add_argument(
        "--encrypt",
        type=str,
        metavar="FILE",
        help="Encrypt a file (non-interactive mode)"
    )
    parser.add_argument(
        "--decrypt",
        type=str,
        metavar="FILE",
        help="Decrypt a file (non-interactive mode)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="FILE",
        help="Output file path (optional)"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete original file after encryption/decryption"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch GUI application"
    )
    
    args = parser.parse_args()
    
    key_mgr = MasterKeyManager()
    
    try:
        # First time setup if not initialized
        if not key_mgr.is_initialized():
            if not setup_master_password_cli(key_mgr):
                key_mgr.lock()
                sys.exit(1)
        else:
            # Unlock with master password
            if not unlock_with_master_password_cli(key_mgr):
                print("Authentication failed. Exiting.")
                key_mgr.lock()
                sys.exit(1)
        
        # Handle encrypt mode
        if args.encrypt:
            success = encrypt_file_non_interactive(
                key_mgr,
                args.encrypt,
                args.output,
                args.delete
            )
            key_mgr.lock()
            sys.exit(0 if success else 1)
        
        # Handle decrypt mode
        if args.decrypt:
            success = decrypt_file_non_interactive(
                key_mgr,
                args.decrypt,
                args.output,
                args.delete,
                overwrite=False
            )
            key_mgr.lock()
            sys.exit(0 if success else 1)
        
        # Interactive mode (default)
        main_menu_cli(key_mgr)

    except KeyboardInterrupt:
        print("\n\nLocking...")
        print("Interrupted by user. Exiting.")
        key_mgr.lock()
        sys.exit(0)
    except (OSError, ValueError, RuntimeError) as e:
        print(f"An error occurred: {e}")
        key_mgr.lock()
        sys.exit(1)
    finally:
        # Ensure key is always cleared on exit
        key_mgr.lock()
