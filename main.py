#!/usr/bin/env python3
"""
Main entry point for LPES (Local Production Environment Simulator).
"""

import sys
import os
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lpes.cli.main import cli

if __name__ == '__main__':
    cli()
