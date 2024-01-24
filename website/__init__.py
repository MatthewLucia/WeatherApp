"""
__init.py__ - Flask Application Factory

This file defines the Flask application factory function `create_app`.
The application is configured with settings such as a secret key and session options.
It also registers blueprints for different parts of the application.

Author: Matt Lucia
"""

from flask import Flask


def create_app():
    # Create a Flask application
    app = Flask(__name__)

    # Configure session secret key and settings
    app.config['SECRET_KEY'] = '&jL82hB%#h@k!9l!h'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True

    # Import and register blueprints for different parts of the application
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app # Return configured Flask application
