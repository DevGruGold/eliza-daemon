#!/usr/bin/env python3
"""
Basic tests for Eliza Daemon components
Run with: python test_eliza.py
"""

import asyncio
import json
import os
from pathlib import Path

def test_config_exists():
    """Test that configuration files exist"""
    print("🔍 Testing configuration files...")

    config_files = ['config.json', '.env.example', 'requirements.txt']
    for file in config_files:
        if Path(file).exists():
            print(f"  ✅ {file} exists")
        else:
            print(f"  ❌ {file} missing")

def test_modules_import():
    """Test that all modules can be imported"""
    print("\n🔍 Testing module imports...")

    try:
        from agent.langchain_brain import ElizaAgent
        print("  ✅ ElizaAgent imports successfully")
    except ImportError as e:
        print(f"  ❌ ElizaAgent import failed: {e}")

    modules = [
        'tasks.monitor_twitter',
        'tasks.monitor_miners', 
        'tasks.handle_rewards',
        'tasks.governance_agent',
        'tasks.notify_discord',
        'memory.supabase_memory'
    ]

    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module} imports successfully")
        except ImportError as e:
            print(f"  ❌ {module} import failed: {e}")

def test_config_structure():
    """Test configuration file structure"""
    print("\n🔍 Testing configuration structure...")

    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        required_keys = [
            'OPENAI_API_KEY',
            'TWITTER_BEARER_TOKEN', 
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'DISCORD_WEBHOOK'
        ]

        for key in required_keys:
            if key in config:
                print(f"  ✅ {key} configured")
            else:
                print(f"  ⚠️ {key} missing from config")

    except Exception as e:
        print(f"  ❌ Config test failed: {e}")

async def test_eliza_daemon():
    """Test basic daemon functionality"""
    print("\n🔍 Testing Eliza Daemon...")

    try:
        from eliza_daemon import eliza_loop
        print("  ✅ Daemon imports successfully")
        print("  ⚠️ Use 'python eliza_daemon.py' to run full daemon")
    except ImportError as e:
        print(f"  ❌ Daemon import failed: {e}")

def main():
    """Run all tests"""
    print("🦾 ELIZA DAEMON - SYSTEM TESTS")
    print("=" * 50)

    test_config_exists()
    test_modules_import()
    test_config_structure()

    # Run async test
    try:
        asyncio.run(test_eliza_daemon())
    except Exception as e:
        print(f"❌ Async test failed: {e}")

    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Configure API keys in config.json")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run daemon: python eliza_daemon.py")
    print("4. Monitor logs: tail -f logs/eliza.log")

if __name__ == "__main__":
    main()
