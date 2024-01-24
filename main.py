"""
main.py - Main script to run the Flask web application.

This script creates the Flask app using the create_app function from the website package.
If this script is run directly (not imported), it starts the app in debug mode.

Author: Matt Lucia
Date: January 23, 2024
"""

from website import create_app

# Create Flask app
app = create_app()

if __name__ == '__main__': # Run app in debug mode if script is being run directly (not imported)
    app.run(debug=True)