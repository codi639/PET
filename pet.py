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

    args = parser.parse_args()

    # Default to CLI if no option specified
    if args.gui:
        try:
            from interface import run_gui
            run_gui()
        except ImportError as e:
            print("Error: Failed to load GUI. Make sure customtkinter is installed.")
            print("Install with: pip install customtkinter")
            print(f"\nDetails: {e}")
            sys.exit(1)
    else:
        from interface import run_cli
        run_cli()


if __name__ == "__main__":
    main()
