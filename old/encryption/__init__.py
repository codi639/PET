"""
Encryption module for PET - Python Encryption Tool.
Handles file encryption and decryption using ChaCha20-Poly1305.
"""

from .file_crypto import encrypt_file, decrypt_file
from .constants import PET_EXTENSION, PET_MAGIC, PET_VERSION

__all__ = ['encrypt_file', 'decrypt_file', 'PET_EXTENSION', 'PET_MAGIC', 'PET_VERSION']
