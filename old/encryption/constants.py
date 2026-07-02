"""
Constants for PET file format and encryption.
"""

# File extension for encrypted files
PET_EXTENSION = '.pet'

# Magic bytes to identify PET encrypted files
# Format: 'PET' + signature bytes + version marker (8 bytes total)
# Using 0xAE (® symbol region) and 0x42 for uniqueness
PET_MAGIC = b'PET\xAE\x42\xF1\x01\x00'

# Current file format version
PET_VERSION = 1

# Encryption parameters
NONCE_SIZE = 12  # ChaCha20-Poly1305 nonce size (96 bits)
TAG_SIZE = 16    # Poly1305 authentication tag size (128 bits)
CHUNK_SIZE = 64 * 1024  # 64 KB chunks for reading/writing files

# File format:
# [8 bytes: magic "PET\xAE\x42\xF1\x01\x00"]
# [1 byte: version]
# [12 bytes: nonce]
# [2 bytes: original filename length (big-endian)]
# [variable: original filename (UTF-8)]
# [variable: encrypted data + 16-byte auth tag]
