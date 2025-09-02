#!/usr/bin/env python3
"""
LPES CLI Entry Point
Main command-line interface for the Local Production Environment Simulator.

This is the production entry point for LPES. It provides a comprehensive
command-line interface for managing local development environments with
production-like features including SSL certificates, custom domains,
reverse proxy, and build management.

Usage:
    python main.py --help
    python main.py init <project_name> --path <path> --build <cmd> --start <cmd>
    python main.py build <project_name>
    python main.py start <project_name>
    python main.py proxy start
"""

import sys
import os
from pathlib import Path

# Add the package to Python path for proper imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

try:
    from lpes.cli.main import cli
except ImportError as e:
    print(f"Error importing LPES CLI: {e}")
    print("Make sure you're running from the correct directory and dependencies are installed.")
    sys.exit(1)

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        print("\n👋 LPES CLI interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
