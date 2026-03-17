# PET - Setup & Usage Guide

## Quick Start

### Standard GUI (Full Features)
```bash
python pet.py --gui
```

### Command Line Interface
```bash
python pet.py --cli
# or just
python pet.py
```

### Quick Encrypt/Decrypt GUI (Tray Version)
```bash
python -m interface.gui_tray
```

---

## Windows Context Menu Setup

### Install Context Menus (Easy Method)

1. **Open Command Prompt or PowerShell** in the PET directory
2. **Right-click** → **Run as administrator**
3. **Double-click** `setup_registry.bat`

OR run in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
powershell -File setup_registry.ps1
```

### What Gets Added

After setup, you can:
- **Right-click any file** → Select "Encrypt with PET"
- **Right-click .pet files** → Select "Decrypt with PET"

Both operations will:
1. Prompt for master password (if not already authenticated)
2. Show file save dialog
3. Ask about deleting the original file

### Uninstall Context Menus

Run in PowerShell (as Administrator):
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
powershell -File setup_registry.ps1 -Uninstall
```

OR run the batch file:
```
setup_registry.bat --uninstall
```

---

## Command Line Usage

### Interactive Mode (Default)
```bash
python pet.py
```
- Full menu-driven interface
- Set up master password on first run
- Encrypt/decrypt with guided steps

### Encrypt a File
```bash
python pet.py --encrypt FILE.txt
python pet.py --encrypt FILE.txt -o OUTPUT.pet
python pet.py --encrypt FILE.txt --delete
```

**Options:**
- `FILE.txt` - File to encrypt
- `-o OUTPUT.pet` - Output file path (optional, defaults to `FILE.txt.pet`)
- `--delete` - Delete original file after encryption

### Decrypt a File
```bash
python pet.py --decrypt FILE.pet
python pet.py --decrypt FILE.pet -o OUTPUT.txt
python pet.py --decrypt FILE.pet --delete
```

**Options:**
- `FILE.pet` - Encrypted file to decrypt
- `-o OUTPUT.txt` - Output file path (optional)
- `--delete` - Delete encrypted file after decryption

### Examples
```bash
# Encrypt and delete original
python pet.py --encrypt "C:\Users\Username\Documents\secret.txt" --delete

# Decrypt without deleting
python pet.py --decrypt "C:\Users\Username\Documents\secret.txt.pet"

# Decrypt with custom output
python pet.py --decrypt backup.pet -o restored_backup.zip
```

---

## GUI Versions

### Full GUI (`--gui`)
Best for:
- First-time setup
- Changing master password
- Manual encrypt/decrypt operations
- Full control and options

Features:
- Master password setup
- Unlock password entry
- Main menu with all options
- Change password dialog
- File selection via dialog

### Tray GUI (`gui_tray.py`)
Best for:
- Quick encrypt/decrypt
- Context menu operations
- Lightweight and minimal
- Minimal window chrome

Features:
- Simple encrypt/decrypt buttons
- Uses native file dialogs
- Quick setup if needed
- Auto-process files from context menu

---

## First-Time Setup

### Step 1: Initialize Master Password
When you run PET for the first time, you'll be prompted to:
1. Create a master password (min 8 characters)
2. Confirm the password
3. The password is stored securely in `pet_master.json`

**⚠️ IMPORTANT:** If you forget your master password, you cannot recover your encrypted files!

### Step 2: Encrypt/Decrypt Files

After initialization, you can:
- **GUI**: Click "Encrypt File" or "Decrypt File" buttons
- **CLI**: Use `--encrypt` or `--decrypt` flags
- **Context Menu**: Right-click files in Windows Explorer

---

## File Format & Security

### Encryption Details
- **Algorithm**: ChaCha20-Poly1305
- **Key Derivation**: Based on master password
- **File Extension**: `.pet`
- **Authenticated Encryption**: Prevents tampering

### File Structure (`.pet`)
```
[Magic Bytes] [Version] [Nonce] [Encrypted Data] [Auth Tag] [Encrypted Filename]
```

### Decryption
- Original filename is stored and restored automatically
- File verification ensures integrity

---

## Troubleshooting

### Script Execution Policy Error
If you get an error about execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
powershell -File setup_registry.ps1
```

### Python Not Found
Ensure Python is in your PATH:
```bash
python --version
```

If not, add Python to PATH or use full path to Python executable.

### Admin Privileges Required
Some operations require administrator:
- Installing context menus (registry modification)
- Accessing protected files

### "Encryption key not available"
This means the key manager couldn't unlock. Make sure:
1. Master password is correct
2. `pet_master.json` file exists and is readable
3. Authentication succeeded before operation

---

## File Recovery

### If Original File Was Deleted
Unfortunately, deleted files cannot be recovered without tools like:
- EaseUS Data Recovery
- Recuva
- Windows File Recovery

This is why PET asks before deletion!

### Backup Important Files First
Always keep backups of important encrypted files before:
- Updating Python/PET
- Making registry changes
- System updates

---

## Security Best Practices

1. **Never share your master password**
   - It unlocks all encrypted files

2. **Keep master password safe**
   - Write it down and store securely
   - Don't save it in password managers (defeats the purpose)

3. **Delete originals carefully**
   - Only use `--delete` if certain
   - Or delete manually after confirming encryption worked

4. **Backup encrypted files**
   - `.pet` files are your encrypted data
   - Keep multiple copies on different drives

5. **Test restoration**
   - Before deleting originals
   - Verify decrypted file matches original

---

## Advanced Usage

### Batch Encryption
```bash
for file in *.txt do (
    python pet.py --encrypt "%file%" --delete
)
```

### Automated Decryption
```powershell
Get-ChildItem -Filter "*.pet" | ForEach-Object {
    python pet.py --decrypt $_.FullName
}
```

### Create Shortcut for Quick Access
1. Right-click on desktop → New → Shortcut
2. Enter: `python -m interface.gui_tray`
3. Name: "PET Quick Encrypt"
4. Click Advanced → Check "Run as administrator"

---

## Uninstalling PET

### Remove Context Menus
```powershell
powershell -File setup_registry.ps1 -Uninstall
```

### Clean Up Files
PET only stores data in:
- `pet_master.json` - Master password hash
- `.pet` - Encrypted files you create

Just delete the PET folder and `pet_master.json`.

Your encrypted files (`.pet`) remain intact and can be opened later.

---

## Support & Questions

For issues or questions:
1. Check the README.md
2. Review error messages carefully
3. Verify file permissions
4. Ensure Python and dependencies are installed
