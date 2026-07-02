"""
PET - Personal Encryption Tool
Graphical User Interface implementation using CustomTkinter.
"""

import sys
from pathlib import Path
from tkinter import messagebox, filedialog
import customtkinter as ctk
from auth.master_key import MasterKeyManager
from encryption import encrypt_file, decrypt_file, PET_EXTENSION
from encryption.file_crypto import EncryptionError, DecryptionError


class PETApp(ctk.CTk):  # type: ignore[misc]
    """Main application window for PET."""

    def __init__(self) -> None:
        super().__init__()

        self.key_mgr = MasterKeyManager()
        self.setup_window()

        # Show appropriate screen
        if not self.key_mgr.is_initialized():
            self.show_setup_screen()
        else:
            self.show_unlock_screen()

    def setup_window(self) -> None:
        """Configure main window."""
        self.title("PET - Python Encryption Tool")
        self.geometry("500x400")

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

    def show_setup_screen(self) -> None:
        """Display first-time setup screen."""
        self.clear_window()

        # Main frame
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="🔐 First Time Setup",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Subtitle
        subtitle = ctk.CTkLabel(
            frame,
            text="Create your master password to secure your files",
            font=ctk.CTkFont(size=12)
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Password input
        password_label = ctk.CTkLabel(frame, text="Master Password:")
        password_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        self.setup_password_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Enter password (min 8 characters)",
            show="●",
            width=300
        )
        self.setup_password_entry.grid(row=3, column=0, padx=20, pady=5)

        # Confirm password input
        confirm_label = ctk.CTkLabel(frame, text="Confirm Password:")
        confirm_label.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")

        self.setup_confirm_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Re-enter password",
            show="●",
            width=300
        )
        self.setup_confirm_entry.grid(row=5, column=0, padx=20, pady=5)

        # Show password toggle
        self.show_pass_var = ctk.BooleanVar()
        show_pass_check = ctk.CTkCheckBox(
            frame,
            text="Show password",
            variable=self.show_pass_var,
            command=self.toggle_password_visibility_setup
        )
        show_pass_check.grid(row=6, column=0, padx=20, pady=10)

        # Create button
        create_btn = ctk.CTkButton(
            frame,
            text="Create Master Password",
            command=self.handle_setup,
            height=40
        )
        create_btn.grid(row=7, column=0, padx=20, pady=20)

        # Warning label
        warning = ctk.CTkLabel(
            frame,
            text="⚠️ Keep this password safe. It cannot be recovered if lost.",
            font=ctk.CTkFont(size=10),
            text_color="yellow"
        )
        warning.grid(row=8, column=0, padx=20, pady=(0, 20))

        # Bind Enter key
        self.setup_confirm_entry.bind("<Return>", lambda e: self.handle_setup())  # type: ignore[arg-type]

    def toggle_password_visibility_setup(self) -> None:
        """Toggle password visibility for setup screen."""
        show = "" if self.show_pass_var.get() else "●"
        self.setup_password_entry.configure(show=show)  # type: ignore[call-arg]
        self.setup_confirm_entry.configure(show=show)  # type: ignore[call-arg]

    def handle_setup(self) -> None:
        """Handle master password creation."""
        password = self.setup_password_entry.get()
        confirm = self.setup_confirm_entry.get()

        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters for security.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        if self.key_mgr.initialize(password):
            messagebox.showinfo(
                "Success",
                "Master password created successfully!\n\nYou can now encrypt and decrypt files."
            )
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Failed to initialize master password.")

    def show_unlock_screen(self) -> None:
        """Display unlock screen."""
        self.clear_window()

        # Main frame
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="🔐 PET",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Subtitle
        subtitle = ctk.CTkLabel(
            frame,
            text="Python Encryption Tool",
            font=ctk.CTkFont(size=14)
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 30))

        # Password label
        password_label = ctk.CTkLabel(frame, text="Enter Master Password:")
        password_label.grid(row=2, column=0, padx=20, pady=(10, 5))

        # Password entry
        self.unlock_password_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Master password",
            show="●",
            width=300
        )
        self.unlock_password_entry.grid(row=3, column=0, padx=20, pady=10)
        self.unlock_password_entry.focus()

        # Unlock button
        unlock_btn = ctk.CTkButton(
            frame,
            text="Unlock",
            command=self.handle_unlock,
            height=40,
            width=150
        )
        unlock_btn.grid(row=4, column=0, padx=20, pady=20)

        # Bind Enter key
        self.unlock_password_entry.bind("<Return>", lambda e: self.handle_unlock())  # type: ignore[arg-type]

    def handle_unlock(self) -> None:
        """Handle unlock attempt."""
        password = self.unlock_password_entry.get()

        if self.key_mgr.unlock(password):
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid master password.")
            self.unlock_password_entry.delete(0, 'end')

    def show_main_menu(self) -> None:
        """Display main menu screen."""
        self.clear_window()

        # Main frame
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="🔓 Unlocked",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Encrypt file button
        encrypt_btn = ctk.CTkButton(
            frame,
            text="🔒 Encrypt File",
            command=self.encrypt_file,
            height=50,
            width=250,
            font=ctk.CTkFont(size=14)
        )
        encrypt_btn.grid(row=1, column=0, padx=20, pady=10)

        # Decrypt file button
        decrypt_btn = ctk.CTkButton(
            frame,
            text="🔓 Decrypt File",
            command=self.decrypt_file,
            height=50,
            width=250,
            font=ctk.CTkFont(size=14)
        )
        decrypt_btn.grid(row=2, column=0, padx=20, pady=10)

        # Change password button
        change_pass_btn = ctk.CTkButton(
            frame,
            text="🔑 Change Master Password",
            command=self.show_change_password,
            height=40,
            width=250
        )
        change_pass_btn.grid(row=3, column=0, padx=20, pady=10)

        # Lock and exit button
        lock_btn = ctk.CTkButton(
            frame,
            text="Lock and Exit",
            command=self.lock_and_exit,
            height=40,
            width=150,
            fg_color="gray",
            hover_color="darkgray"
        )
        lock_btn.grid(row=4, column=0, padx=20, pady=(30, 20))

    def encrypt_file(self) -> None:
        """Handle file encryption with file dialog."""
        # Open file dialog to select file to encrypt
        file_path = filedialog.askopenfilename(
            title="Select file to encrypt",
            parent=self
        )
        
        if not file_path:
            return  # User cancelled
        
        # Check if file is already encrypted
        if file_path.lower().endswith(PET_EXTENSION):
            messagebox.showerror(
                "Error",
                f"File is already encrypted (has {PET_EXTENSION} extension)."
            )
            return
        
        # Get output path from save dialog
        output_file = filedialog.asksaveasfilename(
            title="Save encrypted file as",
            defaultextension=PET_EXTENSION,
            initialfile=Path(file_path).name + PET_EXTENSION,
            filetypes=[("PET Files", f"*{PET_EXTENSION}"), ("All Files", "*.*")],
            parent=self
        )
        
        if not output_file:
            return  # User cancelled
        
        # Check if output file already exists
        if Path(output_file).exists():
            response = messagebox.askyesno(
                "File exists",
                f"File already exists. Overwrite it?"
            )
            if not response:
                return
            try:
                Path(output_file).unlink()
            except OSError as e:
                messagebox.showerror("Error", f"Could not delete existing file: {e}")
                return
        
        # Get encryption key
        encryption_key = self.key_mgr.get_encryption_key()
        if not encryption_key:
            messagebox.showerror("Error", "Encryption key not available. Please unlock first.")
            return
        
        try:
            # Show progress
            encrypt_file(file_path, output_file, encryption_key)
            
            # Ask if user wants to delete original file
            response = messagebox.askyesno(
                "Success",
                f"File encrypted successfully!\n\nDelete original file?"
            )
            
            if response:
                try:
                    Path(file_path).unlink()
                    messagebox.showinfo("Success", "Original file deleted.")
                except OSError as e:
                    messagebox.showwarning(
                        "Warning",
                        f"File encrypted but could not delete original: {e}"
                    )
            else:
                messagebox.showinfo(
                    "Success",
                    f"File encrypted successfully!\n\nEncrypted file: {output_file}"
                )
        
        except FileNotFoundError:
            messagebox.showerror("Error", "Input file not found.")
        except EncryptionError as e:
            messagebox.showerror("Encryption Error", f"Failed to encrypt file: {e}")
        except (OSError, ValueError) as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def decrypt_file(self) -> None:
        """Handle file decryption with file dialog."""
        # Open file dialog to select file to decrypt
        file_path = filedialog.askopenfilename(
            title="Select file to decrypt",
            filetypes=[(f"PET Files (*{PET_EXTENSION})", f"*{PET_EXTENSION}"), ("All Files", "*.*")],
            parent=self
        )
        
        if not file_path:
            return  # User cancelled
        
        # Warn if not a .pet file
        if not file_path.lower().endswith(PET_EXTENSION):
            response = messagebox.askyesno(
                "Warning",
                f"File does not have {PET_EXTENSION} extension.\n\nContinue anyway?"
            )
            if not response:
                return
        
        # Determine default output path
        if file_path.lower().endswith(PET_EXTENSION):
            default_output = file_path[:-len(PET_EXTENSION)]
        else:
            default_output = file_path + ".decrypted"
        
        # Get output path from save dialog
        output_file = filedialog.asksaveasfilename(
            title="Save decrypted file as",
            initialfile=Path(default_output).name,
            initialdir=Path(default_output).parent,
            filetypes=[("All Files", "*.*")],
            parent=self
        )
        
        if not output_file:
            return  # User cancelled
        
        # Check if output file already exists
        if Path(output_file).exists():
            response = messagebox.askyesno(
                "File exists",
                f"File already exists. Overwrite it?"
            )
            if not response:
                return
            try:
                Path(output_file).unlink()
            except OSError as e:
                messagebox.showerror("Error", f"Could not delete existing file: {e}")
                return
        
        # Get encryption key
        encryption_key = self.key_mgr.get_encryption_key()
        if not encryption_key:
            messagebox.showerror("Error", "Encryption key not available. Please unlock first.")
            return
        
        try:
            # Decrypt file
            decrypt_file(file_path, output_file, encryption_key, overwrite=True)
            
            # Ask if user wants to delete encrypted file
            response = messagebox.askyesno(
                "Success",
                f"File decrypted successfully!\n\nDelete encrypted file?"
            )
            
            if response:
                try:
                    Path(file_path).unlink()
                    messagebox.showinfo("Success", "Encrypted file deleted.")
                except OSError as e:
                    messagebox.showwarning(
                        "Warning",
                        f"File decrypted but could not delete encrypted file: {e}"
                    )
            else:
                messagebox.showinfo(
                    "Success",
                    f"File decrypted successfully!\n\nDecrypted file: {output_file}"
                )
        
        except FileNotFoundError:
            messagebox.showerror("Error", "Input file not found.")
        except DecryptionError as e:
            messagebox.showerror("Decryption Error", f"Failed to decrypt file: {e}")
        except (OSError, ValueError) as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def show_change_password(self) -> None:
        """Display change password dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Change Master Password")
        dialog.geometry("400x350")
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Current password
        current_label = ctk.CTkLabel(dialog, text="Current Password:")
        current_label.pack(padx=20, pady=(20, 5))

        current_entry = ctk.CTkEntry(dialog, show="●", width=250)
        current_entry.pack(padx=20, pady=5)

        # New password
        new_label = ctk.CTkLabel(dialog, text="New Password:")
        new_label.pack(padx=20, pady=(15, 5))

        new_entry = ctk.CTkEntry(dialog, show="●", width=250)
        new_entry.pack(padx=20, pady=5)

        # Confirm new password
        confirm_label = ctk.CTkLabel(dialog, text="Confirm New Password:")
        confirm_label.pack(padx=20, pady=(15, 5))

        confirm_entry = ctk.CTkEntry(dialog, show="●", width=250)
        confirm_entry.pack(padx=20, pady=5)  # type: ignore[call-arg]

        def handle_change() -> None:
            current = current_entry.get()
            new = new_entry.get()
            confirm = confirm_entry.get()

            if len(new) < 8:
                messagebox.showerror("Error", "New password must be at least 8 characters.")
                return

            if new != confirm:
                messagebox.showerror("Error", "New passwords do not match.")
                return

            if self.key_mgr.change_password(current, new):
                messagebox.showinfo("Success", "Master password changed successfully!")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to change password. Current password may be incorrect.")

        # Change button
        change_btn = ctk.CTkButton(
            dialog,
            text="Change Password",
            command=handle_change,
            height=40
        )
        change_btn.pack(padx=20, pady=20)

        # Bind Enter key
        confirm_entry.bind("<Return>", lambda e: handle_change())  # type: ignore[arg-type]

    def lock_and_exit(self) -> None:
        """Lock the key manager and exit."""
        self.key_mgr.lock()
        self.quit()


def run_gui() -> None:
    """Main entry point for GUI interface."""
    app = None
    try:
        app = PETApp()
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
