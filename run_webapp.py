#!/usr/bin/env python3
"""
Startup script for the Slap Red Scraper web application.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the Flask app
from src.ui.app import app

if __name__ == '__main__':
    print("🔍 Starting Slap Red Scraper Web Application...")
    print("📍 Access the application at: http://localhost:12000")
    print("🔑 Use the credentials from In/config.ini to log in")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Ensure required directories exist
    os.makedirs('out', exist_ok=True)
    os.makedirs('In', exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=12000, debug=True)