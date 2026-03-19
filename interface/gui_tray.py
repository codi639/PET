"""
PET - Personal Encryption Tool
Minimal GUI for system tray and context menu operations.
"""

##################################
#           DEPRECATED           #
##################################

import sys
import argparse
from pathlib import Path
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageDraw
from io import BytesIO
import getpass
from auth.master_key import MasterKeyManager
from encryption import encrypt_file, decrypt_file, PET_EXTENSION
from encryption.file_crypto import EncryptionError, DecryptionError


class PETTrayApp(ctk.CTk):  # type: ignore[misc]
    """Minimal application window for PET with system tray integration."""

    def __init__(self, file_path: str | None = None, operation: str | None = None) -> None:
        super().__init__()

        self.key_mgr = MasterKeyManager()
        self.file_path = file_path
        self.operation = operation  # "encrypt" or "decrypt"
        self.locked = True

        self.setup_window()

        # Try to unlock if we have a file to process
        if self.file_path:
            self.authenticate_and_process()
        else:
            self.show_main_screen()

    def setup_window(self) -> None:
        """Configure main window."""
        self.title("PET - Quick Encrypt/Decrypt")
        self.geometry("400x200")
        self.resizable(False, False)

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def clear_window(self) -> None:
        """Remove all widgets from window."""
        for widget in self.winfo_children():
            widget.destroy()

    def authenticate_and_process(self) -> None:
        """Authenticate user for file operations."""
        # First time setup if not initialized
        if not self.key_mgr.is_initialized():
            self.show_setup_screen()
            return

        # Unlock with master password
        self.show_unlock_screen()

    def show_setup_screen(self) -> None:
        """Display first-time setup screen."""
        self.clear_window()
        self.geometry("450x300")

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="🔐 First Time Setup",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        subtitle = ctk.CTkLabel(
            frame,
            text="Create your master password",
            font=ctk.CTkFont(size=11)
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 15))

        password_label = ctk.CTkLabel(frame, text="Master Password:")
        password_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        self.setup_password_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Min 8 characters",
            show="●",
            width=300
        )
        self.setup_password_entry.grid(row=3, column=0, padx=20, pady=5)

        confirm_label = ctk.CTkLabel(frame, text="Confirm Password:")
        confirm_label.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")

        self.setup_confirm_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Re-enter password",
            show="●",
            width=300
        )
        self.setup_confirm_entry.grid(row=5, column=0, padx=20, pady=5)

        create_btn = ctk.CTkButton(
            frame,
            text="Create & Continue",
            command=self.handle_setup,
            height=40
        )
        create_btn.grid(row=6, column=0, padx=20, pady=20)

        self.setup_confirm_entry.bind("<Return>", lambda e: self.handle_setup())  # type: ignore[arg-type]

    def handle_setup(self) -> None:
        """Handle master password creation."""
        password = self.setup_password_entry.get()
        confirm = self.setup_confirm_entry.get()

        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        if self.key_mgr.initialize(password):
            messagebox.showinfo("Success", "Master password created!")
            if self.file_path:
                self.show_unlock_screen()
            else:
                self.show_main_screen()
        else:
            messagebox.showerror("Error", "Failed to initialize.")

    def show_unlock_screen(self) -> None:
        """Display unlock screen."""
        self.clear_window()
        self.geometry("400x200")

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="🔐 Unlock PET",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 30))

        password_label = ctk.CTkLabel(frame, text="Master Password:")
        password_label.grid(row=1, column=0, padx=20, pady=(10, 5))

        self.unlock_password_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Enter password",
            show="●",
            width=250
        )
        self.unlock_password_entry.grid(row=2, column=0, padx=20, pady=10)
        self.unlock_password_entry.focus()

        unlock_btn = ctk.CTkButton(
            frame,
            text="Unlock",
            command=self.handle_unlock,
            height=40,
            width=150
        )
        unlock_btn.grid(row=3, column=0, padx=20, pady=20)

        self.unlock_password_entry.bind("<Return>", lambda e: self.handle_unlock())  # type: ignore[arg-type]

    def handle_unlock(self) -> None:
        """Handle unlock attempt."""
        password = self.unlock_password_entry.get()

        if self.key_mgr.unlock(password):
            self.locked = False
            if self.file_path:
                self.process_file()
            else:
                self.show_main_screen()
        else:
            messagebox.showerror("Error", "Invalid password.")
            self.unlock_password_entry.delete(0, 'end')

    def show_main_screen(self) -> None:
        """Display main menu screen."""
        self.clear_window()
        self.geometry("400x250")

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="🔓 PET",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 30))

        encrypt_btn = ctk.CTkButton(
            frame,
            text="🔒 Encrypt File",
            command=self.encrypt_file_dialog,
            height=50,
            width=250,
            font=ctk.CTkFont(size=13)
        )
        encrypt_btn.grid(row=1, column=0, padx=20, pady=10)

        decrypt_btn = ctk.CTkButton(
            frame,
            text="🔓 Decrypt File",
            command=self.decrypt_file_dialog,
            height=50,
            width=250,
            font=ctk.CTkFont(size=13)
        )
        decrypt_btn.grid(row=2, column=0, padx=20, pady=10)

        exit_btn = ctk.CTkButton(
            frame,
            text="Lock & Exit",
            command=self.lock_and_exit,
            height=40,
            width=150,
            fg_color="gray",
            hover_color="darkgray"
        )
        exit_btn.grid(row=3, column=0, padx=20, pady=(30, 20))

    def encrypt_file_dialog(self) -> None:
        """Open file dialog to select file for encryption."""
        file_path = filedialog.askopenfilename(
            title="Select file to encrypt",
            parent=self
        )

        if not file_path:
            return

        self.file_path = file_path
        self.operation = "encrypt"
        self.show_encrypt_options()

    def decrypt_file_dialog(self) -> None:
        """Open file dialog to select file for decryption."""
        file_path = filedialog.askopenfilename(
            title="Select file to decrypt",
            filetypes=[(f"PET Files (*{PET_EXTENSION})", f"*{PET_EXTENSION}"), ("All Files", "*.*")],
            parent=self
        )

        if not file_path:
            return

        if not file_path.lower().endswith(PET_EXTENSION):
            response = messagebox.askyesno(
                "Warning",
                f"File does not have {PET_EXTENSION} extension. Continue?"
            )
            if not response:
                return

        self.file_path = file_path
        self.operation = "decrypt"
        self.show_decrypt_options()

    def show_encrypt_options(self) -> None:
        """Show encryption options dialog."""
        if not self.file_path:
            return

        # Create output path suggestion
        output_path = self.file_path + PET_EXTENSION

        # Ask about output location
        output_file = filedialog.asksaveasfilename(
            title="Save encrypted file as",
            defaultextension=PET_EXTENSION,
            initialfile=Path(self.file_path).name + PET_EXTENSION,
            initialdir=Path(self.file_path).parent,
            filetypes=[("PET Files", f"*{PET_EXTENSION}"), ("All Files", "*.*")],
            parent=self
        )

        if not output_file:
            return

        # Check if file exists
        if Path(output_file).exists():
            response = messagebox.askyesno(
                "File exists",
                f"Overwrite '{Path(output_file).name}'?"
            )
            if not response:
                return
            try:
                Path(output_file).unlink()
            except OSError as e:
                messagebox.showerror("Error", f"Could not delete existing file: {e}")
                return

        # Perform encryption
        self.perform_encryption(output_file)

    def show_decrypt_options(self) -> None:
        """Show decryption options dialog."""
        if not self.file_path:
            return

        # Determine default output
        if self.file_path.lower().endswith(PET_EXTENSION):
            default_output = self.file_path[:-len(PET_EXTENSION)]
        else:
            default_output = self.file_path + ".decrypted"

        # Ask about output location
        output_file = filedialog.asksaveasfilename(
            title="Save decrypted file as",
            initialfile=Path(default_output).name,
            initialdir=Path(default_output).parent,
            filetypes=[("All Files", "*.*")],
            parent=self
        )

        if not output_file:
            return

        # Check if file exists
        if Path(output_file).exists():
            response = messagebox.askyesno(
                "File exists",
                f"Overwrite '{Path(output_file).name}'?"
            )
            if not response:
                return
            try:
                Path(output_file).unlink()
            except OSError as e:
                messagebox.showerror("Error", f"Could not delete existing file: {e}")
                return

        # Perform decryption
        self.perform_decryption(output_file)

    def perform_encryption(self, output_path: str) -> None:
        """Perform file encryption."""
        if not self.file_path:
            return

        encryption_key = self.key_mgr.get_encryption_key()
        if not encryption_key:
            messagebox.showerror("Error", "Encryption key not available.")
            self.lock_and_exit()
            return
        
        try:
            encrypt_file(self.file_path, output_path, encryption_key)
            
            # Ask about deleting original
            response = messagebox.askyesno(
                "Success",
                f"File encrypted successfully!\n\nDelete original file?"
            )
            
            if response:
                try:
                    Path(self.file_path).unlink()
                except OSError as e:
                    messagebox.showwarning("Warning", f"Could not delete original: {e}")
            
            self.lock_and_exit()
        
        except (EncryptionError, FileNotFoundError, OSError, ValueError) as e:
            messagebox.showerror("Encryption Error", f"Failed to encrypt: {e}")
            self.lock_and_exit()

    def perform_decryption(self, output_path: str) -> None:
        """Perform file decryption."""
        if not self.file_path:
            return
        
        encryption_key = self.key_mgr.get_encryption_key()
        if not encryption_key:
            messagebox.showerror("Error", "Encryption key not available.")
            self.lock_and_exit()
            return
        
        try:
            decrypt_file(self.file_path, output_path, encryption_key, overwrite=True)
            
            # Ask about deleting encrypted file
            response = messagebox.askyesno(
                "Success",
                f"File decrypted successfully!\n\nDelete encrypted file?"
            )
            
            if response:
                try:
                    Path(self.file_path).unlink()
                except OSError as e:
                    messagebox.showwarning("Warning", f"Could not delete encrypted: {e}")
            
            self.lock_and_exit()
        
        except (DecryptionError, FileNotFoundError, OSError, ValueError) as e:
            messagebox.showerror("Decryption Error", f"Failed to decrypt: {e}")
            self.lock_and_exit()

    def process_file(self) -> None:
        """Process file based on operation (called from command-line args)."""
        if not self.file_path:
            return
        
        if not Path(self.file_path).exists():
            messagebox.showerror("Error", f"File not found: {self.file_path}")
            self.lock_and_exit()
            return
        
        if self.operation == "encrypt":
            # Direct encryption without file dialogs
            output_path = self.file_path + PET_EXTENSION
            if Path(output_path).exists():
                try:
                    Path(output_path).unlink()
                except OSError as e:
                    messagebox.showerror("Error", f"Could not delete existing file: {e}")
                    self.lock_and_exit()
                    return
            self.perform_encryption(output_path)
        elif self.operation == "decrypt":
            # Direct decryption without file dialogs
            if self.file_path.lower().endswith(PET_EXTENSION):
                output_path = self.file_path[:-len(PET_EXTENSION)]
            else:
                output_path = self.file_path + ".decrypted"
            self.perform_decryption(output_path)
        else:
            self.show_main_screen()

    def lock_and_exit(self) -> None:
        """Lock the key manager and exit."""
        self.key_mgr.lock()
        self.quit()


def run_gui_tray() -> None:
    """Main entry point for tray GUI interface."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="PET - Quick Encrypt/Decrypt",
        prog="pet-tray"
    )
    parser.add_argument(
        "--encrypt",
        type=str,
        metavar="FILE",
        help="Encrypt a file"
    )
    parser.add_argument(
        "--decrypt",
        type=str,
        metavar="FILE",
        help="Decrypt a file"
    )
    
    args = parser.parse_args()
    
    file_path = args.encrypt or args.decrypt
    operation = "encrypt" if args.encrypt else ("decrypt" if args.decrypt else None)
    
    app = None
    try:
        app = PETTrayApp(file_path, operation)
        app.mainloop()
    except (ImportError, RuntimeError, OSError) as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        if app:
            app.key_mgr.lock()
        sys.exit(1)
    except KeyboardInterrupt:
        if app:
            app.key_mgr.lock()
        sys.exit(0)
    finally:
        # Ensure key is always cleared on exit
        if app:
            app.key_mgr.lock()
