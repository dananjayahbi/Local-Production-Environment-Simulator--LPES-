#!/usr/bin/env python3
"""
LPES GUI Launcher Module

This module provides the entry point for the LPES GUI application.
"""

import sys
import os
from pathlib import Path

def main():
    """Launch the LPES GUI application."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    gui_dir = project_root / "gui"
    
    # Add directories to path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_dir))
    sys.path.insert(0, str(gui_dir))
    
    try:
        # Import and run the GUI
        from lpes_gui_enhanced import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"Error importing GUI module: {e}")
        print(f"Searched paths: {[str(project_root), str(src_dir), str(gui_dir)]}")
        print("Please ensure LPES is properly installed and all dependencies are available.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
