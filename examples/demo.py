#!/usr/bin/env python3
"""
LPES Demo Script - Demonstrates complete functionality.
"""

import asyncio
import time
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and display output."""
    print(f"\n🔧 {description}")
    print(f"💻 Command: {cmd}")
    print("─" * 50)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"⚠️  stderr: {result.stderr}")
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
    else:
        print("✅ Command completed successfully")
    
    return result.returncode == 0

def demo_lpes():
    """Demonstrate LPES functionality."""
    print("🚀 LPES (Local Production Environment Simulator) Demo")
    print("=" * 60)
    
    # Change to LPES directory
    lpes_dir = Path(__file__).parent
    original_dir = Path.cwd()
    
    try:
        print(f"📁 Working directory: {lpes_dir}")
        
        # Test 1: Show help
        run_command("python main.py --help", "Display LPES help")
        
        # Test 2: List projects (should be empty initially)
        run_command("python main.py list", "List projects (initial state)")
        
        # Test 3: Initialize a project
        run_command(
            'python main.py init demo-app --path ./test-project --build "echo \'Demo build\'" --start "echo \'Demo server running on port 3000\' && timeout 5"',
            "Initialize demo project"
        )
        
        # Test 4: Add domain
        run_command(
            "python main.py domain add demo-app demo.local --ssl",
            "Add domain with SSL"
        )
        
        # Test 5: List domains
        run_command("python main.py domain list", "List domains")
        
        # Test 6: Build project
        run_command("python main.py build demo-app", "Build project")
        
        # Test 7: List SSL certificates
        run_command("python main.py ssl list", "List SSL certificates")
        
        # Test 8: Show trust instructions
        run_command("python main.py ssl trust-info", "Show SSL trust instructions")
        
        # Test 9: List projects (should show the demo project)
        run_command("python main.py list", "List projects (after setup)")
        
        # Test 10: Clean up
        print("\n🧹 Cleaning up demo project...")
        subprocess.run("echo y | python main.py remove demo-app --cleanup", shell=True)
        
        print("\n🎉 LPES Demo completed successfully!")
        print("\n📖 Next steps:")
        print("1. Create a real NextJS project")
        print("2. Initialize it with LPES: lpes init myapp --path /path/to/project --build 'npm run build' --start 'npm start'")
        print("3. Add a domain: lpes domain add myapp myapp.local --ssl --hosts-file")
        print("4. Start your project: lpes start myapp")
        print("5. Start the proxy: lpes proxy start")
        print("6. Access via HTTPS: https://myapp.local")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Change to script directory
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)
    
    success = demo_lpes()
    sys.exit(0 if success else 1)
