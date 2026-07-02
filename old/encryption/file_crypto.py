"""
File encryption and decryption using ChaCha20-Poly1305.
"""

import os
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305  # type: ignore[import-untyped]

from .constants import (
    PET_EXTENSION,
    PET_MAGIC,
    PET_VERSION,
    NONCE_SIZE
)


class EncryptionError(Exception):
    """Base exception for encryption-related errors."""


class DecryptionError(Exception):
    """Base exception for decryption-related errors."""


def encrypt_file(
    input_path: str,
    output_path: Optional[str],
    encryption_key: bytes
) -> str:
    """
    Encrypt a file using ChaCha20-Poly1305.

    Args:
        input_path: Path to the file to encrypt
        output_path: Optional output path. If None, appends .pet to input filename
        encryption_key: 32-byte encryption key

    Returns:
        Path to the encrypted file

    Raises:
        EncryptionError: If encryption fails
        FileNotFoundError: If input file doesn't exist
        ValueError: If encryption key is invalid
    """
    if len(encryption_key) != 32:
        raise ValueError("Encryption key must be 32 bytes")

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_file.is_file():
        raise EncryptionError(f"Path is not a file: {input_path}")

    # Determine output path
    if output_path is None:
        output_file = Path(str(input_file) + PET_EXTENSION)
    else:
        output_file = Path(output_path)

    # Check if output already exists
    if output_file.exists():
        raise EncryptionError(f"Output file already exists: {output_file}")

    try:
        # Initialize ChaCha20-Poly1305 cipher
        cipher = ChaCha20Poly1305(encryption_key)

        # Generate random nonce
        nonce = os.urandom(NONCE_SIZE)

        # Get original filename
        original_filename = input_file.name
        filename_bytes = original_filename.encode('utf-8')
        filename_length = len(filename_bytes)

        if filename_length > 65535:
            raise EncryptionError("Filename too long (max 65535 bytes)")

        # Read entire file into memory
        # For large files, consider streaming encryption
        with open(input_file, 'rb') as f:
            plaintext = f.read()

        # Encrypt the data
        # ChaCha20Poly1305 returns ciphertext with auth tag appended
        ciphertext_with_tag = cipher.encrypt(nonce, plaintext, None)

        # Write encrypted file
        with open(output_file, 'wb') as f:
            # Write magic bytes
            f.write(PET_MAGIC)

            # Write version
            f.write(bytes([PET_VERSION]))

            # Write nonce
            f.write(nonce)

            # Write original filename length (2 bytes, big-endian)
            f.write(filename_length.to_bytes(2, byteorder='big'))

            # Write original filename
            f.write(filename_bytes)

            # Write encrypted data with tag
            f.write(ciphertext_with_tag)

        return str(output_file)

    except EncryptionError:
        raise
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt_file(
    input_path: str,
    output_path: Optional[str],
    encryption_key: bytes,
    overwrite: bool = False
) -> str:
    """
    Decrypt a PET encrypted file using ChaCha20-Poly1305.

    Args:
        input_path: Path to the encrypted .pet file
        output_path: Optional output path. If None, strips .pet extension
        encryption_key: 32-byte encryption key
        overwrite: Allow overwriting existing output file

    Returns:
        Path to the decrypted file

    Raises:
        DecryptionError: If decryption fails or file format is invalid
        FileNotFoundError: If input file doesn't exist
        ValueError: If encryption key is invalid
    """
    if len(encryption_key) != 32:
        raise ValueError("Encryption key must be 32 bytes")

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_file.is_file():
        raise DecryptionError(f"Path is not a file: {input_path}")

    try:
        # Read encrypted file
        with open(input_file, 'rb') as f:
            # Read and verify magic bytes
            magic = f.read(8)
            if magic != PET_MAGIC:
                raise DecryptionError("Not a valid PET encrypted file (invalid magic bytes)")

            # Read version
            version = f.read(1)[0]
            if version != PET_VERSION:
                raise DecryptionError(f"Unsupported file version: {version}")

            # Read nonce
            nonce = f.read(NONCE_SIZE)
            if len(nonce) != NONCE_SIZE:
                raise DecryptionError("Corrupted file: incomplete nonce")

            # Read original filename length
            filename_length_bytes = f.read(2)
            if len(filename_length_bytes) != 2:
                raise DecryptionError("Corrupted file: incomplete filename length")
            filename_length = int.from_bytes(filename_length_bytes, byteorder='big')

            # Read original filename
            filename_bytes = f.read(filename_length)
            if len(filename_bytes) != filename_length:
                raise DecryptionError("Corrupted file: incomplete filename")
            original_filename = filename_bytes.decode('utf-8')

            # Read encrypted data with tag
            ciphertext_with_tag = f.read()

        # Determine output path
        if output_path is None:
            # Try to strip .pet extension, or use original filename
            if input_file.suffix.lower() == PET_EXTENSION:
                output_file = Path(str(input_file)[:-len(PET_EXTENSION)])
            else:
                # Use the stored original filename in same directory
                output_file = input_file.parent / original_filename
        else:
            output_file = Path(output_path)

        # Check if output already exists
        if output_file.exists() and not overwrite:
            raise DecryptionError(f"Output file already exists: {output_file}")

        # Initialize ChaCha20-Poly1305 cipher
        cipher = ChaCha20Poly1305(encryption_key)

        # Decrypt the data
        # This will raise an exception if authentication fails
        try:
            plaintext = cipher.decrypt(nonce, ciphertext_with_tag, None)
        except Exception as e:
            raise DecryptionError("Decryption failed: Invalid password or corrupted file") from e

        # Write decrypted file
        with open(output_file, 'wb') as f:
            f.write(plaintext)

        return str(output_file)

    except DecryptionError:
        raise
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {e}") from e


def is_pet_file(file_path: str) -> bool:
    """
    Check if a file is a PET encrypted file.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file has valid PET magic bytes
    """
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(8)
            return magic == PET_MAGIC
    except (OSError, IOError):
        return False
