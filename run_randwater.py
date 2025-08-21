#!/usr/bin/env python3
"""
Startup script for the Randwater Calculator Flask application
"""

from randwater_calculator import app

if __name__ == '__main__':
    print("Starting Randwater Calculator application...")
    print("The application will be available at:")
    print("  - Local: http://localhost:5001")
    print("  - Randwater Admin: http://localhost:5001/admin/randwater")
    print("  - Network: http://[your-ip-address]:5001")
    print("\nPress Ctrl+C to stop the application")
    
    app.run(
        debug=True,
        host='0.0.0.0',  # Makes the app accessible from other devices
        port=5001,
        threaded=True
    )
