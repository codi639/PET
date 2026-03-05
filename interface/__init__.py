"""
Interface package for PET - Python Encryption Tool.
Contains CLI and GUI implementations.
"""

from .cli import run_cli
from .gui import run_gui

__all__ = ['run_cli', 'run_gui']
