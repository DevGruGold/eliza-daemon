#!/usr/bin/env python3
"""
Quick Start Script for Eliza Daemon
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_config():
    """Setup configuration"""
    print("⚙️ Setting up configuration...")

    if not Path("config.json").exists():
        print("❌ config.json not found. Please create it from config.json.template")
        return False

    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        # Check if keys are configured
        placeholder_keys = []
        for key, value in config.items():
            if isinstance(value, str) and ("xxx" in value.lower() or "your-" in value.lower()):
                placeholder_keys.append(key)

        if placeholder_keys:
            print(f"⚠️ Please configure these API keys: {', '.join(placeholder_keys)}")
            return False

        print("✅ Configuration looks good")
        return True

    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def create_logs_dir():
    """Create logs directory"""
    Path("logs").mkdir(exist_ok=True)
    print("✅ Logs directory ready")

def main():
    """Quick start setup"""
    print("🦾 ELIZA DAEMON - QUICK START")
    print("=" * 50)

    if not check_python_version():
        return

    create_logs_dir()

    if not install_dependencies():
        return

    if not setup_config():
        print("\n🔧 CONFIGURATION NEEDED:")
        print("1. Copy config.json.template to config.json") 
        print("2. Add your API keys to config.json")
        print("3. Run this script again")
        return

    print("\n🚀 READY TO LAUNCH!")
    print("Run: python eliza_daemon.py")
    print("Monitor: tail -f logs/eliza.log")

    launch = input("\nLaunch Eliza now? (y/N): ")
    if launch.lower() == 'y':
        print("🦾 Starting Eliza Daemon...")
        os.system("python eliza_daemon.py")

if __name__ == "__main__":
    main()
