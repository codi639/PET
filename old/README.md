# PET - Personal Encryption Tool

A simple, secure file encryption tool using ChaCha20-Poly1305 authenticated encryption.

## Features

- **Strong Encryption**: ChaCha20-Poly1305 authenticated encryption
- **Master Password**: PBKDF2-based key derivation from a single master password
- **Dual Interface**: Command-line (CLI) and graphical (GUI) interfaces
- **Simple Format**: Encrypted files use `.pet` extension with embedded metadata

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface (Default)

```bash
python pet.py
# or explicitly
python pet.py --cli
```

**Encrypt a file:**
1. Run the tool and unlock with your master password
2. Select option 1 (Encrypt file)
3. Enter the file path
4. Encrypted file will be saved with `.pet` extension

**Decrypt a file:**
1. Run the tool and unlock with your master password
2. Select option 2 (Decrypt file)
3. Enter the encrypted file path
4. Original file will be restored

### Graphical Interface

```bash
python pet.py --gui
```

Provides a modern dark-themed interface with the same functionality.

## File Format

Encrypted `.pet` files contain:
- Magic bytes (PET identification)
- Version information
- Encryption nonce
- Original filename (preserved for decryption)
- Encrypted data with authentication tag

## Security

- **Encryption**: ChaCha20-Poly1305 (256-bit key, authenticated encryption)
- **Key Derivation**: PBKDF2-HMAC-SHA256 (100,000 iterations)
- **Master Password**: Minimum 8 characters (recommend 12+ for security)
- **No Password Recovery**: Master password cannot be recovered if lost

## Project Structure

```
PET/
├── auth/              # Authentication and key management
├── encryption/        # File encryption/decryption logic
├── interface/         # CLI and GUI implementations
├── pet.py            # Main entry point
└── requirements.txt  # Python dependencies
```

## License

See LICENSE file for details.


For GUI:

`customtkinter`
