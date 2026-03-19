"""
PET - Personal Encryption Tool
Main entry point - launches CLI or GUI interface.
"""

import sys
import argparse


def main():
    """Main entry point for PET."""
    parser = argparse.ArgumentParser(
        description="PET - Personal Encryption Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch graphical user interface'
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Launch command line interface (default)'
    )
    parser.add_argument(
        '--encrypt',
        type=str,
        metavar='FILE',
        help='Encrypt a file (non-interactive)'
    )
    parser.add_argument(
        '--decrypt',
        type=str,
        metavar='FILE',
        help='Decrypt a file (non-interactive)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        metavar='FILE',
        help='Output file path (optional)'
    )
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete original file after encryption/decryption'
    )

    args = parser.parse_args()

    # GUI mode
    if args.gui:
        try:
            from interface import run_gui
            run_gui()
        except ImportError as e:
            print("Error: Failed to load GUI. Make sure customtkinter is installed.")
            print("Install with: pip install customtkinter")
            print(f"\nDetails: {e}")
            sys.exit(1)
    # Encrypt or decrypt mode (uses GUI tray)
    elif args.encrypt or args.decrypt:
        try:
            from interface import run_gui_tray
            run_gui_tray()
        except ImportError as e:
            print("Error: Failed to load GUI. Make sure customtkinter is installed.")
            print("Install with: pip install customtkinter")
            print(f"\nDetails: {e}")
            sys.exit(1)
    # Default to CLI
    else:
        from interface import run_cli
        run_cli()


if __name__ == "__main__":
    main()
