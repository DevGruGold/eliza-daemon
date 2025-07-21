#!/usr/bin/env python3
"""
Setup script for Eliza Daemon
Run this to prepare your environment for Eliza
"""

import os
import subprocess
import sys

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_environment():
    """Setup environment file"""
    if not os.path.exists(".env"):
        print("🔧 Creating .env file from template...")
        with open(".env.example", "r") as template:
            with open(".env", "w") as env_file:
                env_file.write(template.read())
        print("✅ Please edit .env with your actual API keys!")
    else:
        print("✅ .env file already exists")

def create_logs_dir():
    """Create logs directory"""
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("✅ Created logs directory")

def main():
    print("🦾 Setting up Eliza Daemon...")

    install_requirements()
    setup_environment()
    create_logs_dir()

    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env with your API keys")
    print("2. Run: python eliza_daemon.py")
    print("3. Watch Eliza come to life! 🤖")

if __name__ == "__main__":
    main()
