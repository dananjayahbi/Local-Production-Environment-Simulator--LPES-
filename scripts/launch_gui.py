#!/usr/bin/env python3
"""
LPES GUI Launcher
Quick launcher for the LPES GUI Manager with proper path handling.
"""

import sys
import os
from pathlib import Path

# Get directories
script_dir = Path(__file__).parent
root_dir = script_dir.parent
gui_dir = root_dir / "gui"
src_dir = root_dir / "src"

# Add directories to path
sys.path.extend([str(gui_dir), str(src_dir)])

def main():
    """Launch LPES GUI with error handling."""
    try:
        # Change to root directory
        os.chdir(root_dir)
        
        # Try enhanced GUI first
        from lpes_gui_enhanced import main as gui_main
        print("🚀 Launching LPES GUI Manager Pro...")
        gui_main()
        
    except ImportError:
        try:
            # Fallback to basic GUI
            from lpes_gui import main as gui_main
            print("🚀 Launching LPES GUI Manager...")
            gui_main()
            
        except ImportError as e:
            print(f"❌ Error importing LPES GUI: {e}")
            print("📋 Solutions:")
            print("  1. Install tkinter: Usually included with Python")
            print("  2. Run: pip install -r requirements.txt")
            print("  3. Check Python installation")
            print(f"  4. Run from: {gui_dir}")
            return 1
            
    except Exception as e:
        print(f"💥 GUI error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 GUI launcher interrupted by user")
        sys.exit(0)
