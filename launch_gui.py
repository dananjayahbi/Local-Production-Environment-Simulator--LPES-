#!/usr/bin/env python3
"""
LPES GUI Launcher
Quick launcher for the LPES GUI Manager
"""

import sys
import os
from pathlib import Path

# Add LPES directory to path
lpes_dir = Path(__file__).parent
sys.path.insert(0, str(lpes_dir))

try:
    from lpes_gui import main
    
    if __name__ == "__main__":
        print("🚀 Launching LPES GUI Manager...")
        main()
        
except ImportError as e:
    print(f"❌ Error importing LPES GUI: {e}")
    print("Make sure you're in the LPES directory and all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"💥 Error launching LPES GUI: {e}")
    sys.exit(1)
