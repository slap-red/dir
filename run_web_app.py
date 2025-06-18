#!/usr/bin/env python3
"""
Slap Red Scraper v0.5.4 - Web Interface Launcher
Simple script to start the Flask web application with proper configuration.
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        import flask_login
        print("✅ Flask dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("📦 Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def check_config():
    """Check if configuration file exists."""
    config_path = "In/config.ini"
    if os.path.exists(config_path):
        print(f"✅ Configuration file found: {config_path}")
        return True
    else:
        print(f"❌ Configuration file not found: {config_path}")
        print("📝 Please ensure In/config.ini exists with proper credentials")
        return False

def main():
    """Main function to start the web application."""
    print("🚀 Slap Red Scraper v0.5.4 - Web Interface")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Create necessary directories
    directories = ['data', 'logs', 'cache', 'temp']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Directory ready: {directory}/")
    
    print("\n🌐 Starting web server...")
    print("📍 URL: http://localhost:12000")
    print("🔐 Use credentials from In/config.ini to login")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the web application
    try:
        from web_app import app
        app.run(host='0.0.0.0', port=12000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()