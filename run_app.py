#!/usr/bin/env python3
"""
Simple startup script for the SmartOffer Flask application
"""

from app import app

if __name__ == '__main__':
    print("Starting SmartOffer application...")
    print("The application will be available at:")
    print("  - Local: http://localhost:5000")
    print("  - Network: http://[your-ip-address]:5000")
    print("\nPress Ctrl+C to stop the application")
    
    app.run(
        debug=True,
        host='0.0.0.0',  # Makes the app accessible from other devices
        port=5000,
        threaded=True
    )
