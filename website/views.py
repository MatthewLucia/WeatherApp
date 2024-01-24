"""
views.py - Views Blueprint

This module defines the views blueprint for the Weather Flask app. It includes routes for the home page, dashboard,
search functionality, and historical data.

Author: Matt Lucia
Date: January 23, 2024

"""

from flask import Blueprint, render_template, session, request, flash
import sqlite3
import requests
import geocoder

# Creating a Blueprint named 'views'
views = Blueprint('views', __name__)

# Database filename
DATABASE = 'weather.db'

# Home route
@views.route('/')
def home():
    # Check if the user is logged in
    user = session.get('user')
    if user:
        first_name = session['user']['first_name']
        last_name = session['user']['last_name']
        welcome_message = f"Welcome, {first_name} {last_name}!"
        city = session['user']['city']
        state = session['user']['state']
        try:
            # Get weather data based on user's location
            weather_data, location_data, latitude, longitude = get_weather(
                city, state)
        except Exception:
            # Display flash message if an exception occurs
            flash('Account created. You may need to log in.', category='success')
            return render_template('home.html')
        # Render the home template with weather data
        return render_template("home.html", welcome_message=welcome_message, latitude=latitude, longitude=longitude)
    else:
        return render_template("home.html")

# Dashboard route
@views.route('/dashboard')
def dashboard():
    # Check if the user is logged in
    user = session.get('user')
    if user:
        city = user.get('city', '')
        state = user.get('state', '')
        weather, location, latitude, longitude = get_weather(city, state)
        guest = False
    else:
        # Set default location for guest user
        weather, location, latitude, longitude = get_weather("New York", "NY")
        guest = True
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # Check if weather data exists for the current location
    cur.execute(
        '''SELECT * FROM weather WHERE location = ? LIMIT 1''', (weather[0],))
    output = cur.fetchone()

    # Determine if historical data exists for the current location
    hist_data = True if output else False

    # Render the dashboard template with weather data
    return render_template("dashboard.html", guest=guest, location=location, weather=weather, hist_data=hist_data, latitude=latitude, longitude=longitude)

# Search route
@views.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        city_input = request.form.get('city')
        state = request.form.get('state')
        city = city_input.strip()
        # Set user session for search results
        session['user'] = {
            'user_id': "",
            'email': "",
            'first_name': "Guest",
            'last_name': "",
            'city': city,
            'state': state,
            'preferences': ""
        }
        try:
            # Get weather data based on the searched location
            weather, location, latitude, longitude = get_weather(city, state)
        except Exception as e:
            # Display flash message if an exception occurs during the search
            flash(f"Error, check your spelling and try again.")
            return render_template("search.html")

        user = session.get('user')
        # Determine if the user is a guest or not
        guest = False if user else True

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()

        # Check if weather data exists for the searched location
        cur.execute(
            '''SELECT * FROM weather WHERE location = ? LIMIT 1''', (weather[0],))
        output = cur.fetchone()

        # Determine if historical data exists for the searched location
        hist_data = True if output else False

        # Render the dashboard template with search results
        return render_template("dashboard.html", guest=guest, location=location, weather=weather, hist_data=hist_data, latitude=latitude, longitude=longitude)
    return render_template("search.html")

# TODO: historical data
# Historical data route
@views.route('/historical_data/<location>', methods=['GET', 'POST'])
def historical_data(location):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # Retrieve historical weather data for the specified location
    cur.execute('''SELECT * FROM weather WHERE location = ?''', (location,))
    data = cur.fetchall()

    # Render the historical data template with the retrieved data
    return render_template("historical_data.html", message=data)

# Function to retrieve weather and location data
def get_weather(city, state):
    # Use Bing Maps API to get location coordinates
    g = geocoder.bing(f'{city}, {state}', key='AshcN6RhjXT-3ZKracTUWEY4k0Fp12VFo-TUzIbQO9KI6ecRi-in57eAS-SA4AvS')
    results = g.json
    if not results:
        # Display flash message if location coordinates cannot be retrieved
        flash("Error. Check your internet connection and try again.", category="error")
        return render_template('home.html')
    location = results['address']
    latitude = results['lat']
    longitude = results['lng']

    api_endpoint = f'https://api.weather.gov/points/{latitude},{longitude}'

    # Make the API request
    response = requests.get(api_endpoint)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON data
        json_data = response.json()

        # Access the forecast URL
        forecast_url = json_data['properties']['forecast']

        # Make another request to the forecast URL
        forecast_response = requests.get(forecast_url)

        # Check if the forecast request was successful (status code 200)
        if forecast_response.status_code == 200:
            # Parse the forecast JSON data
            forecast_data = forecast_response.json()

            # Extract relevant weather information
            time_stamp = forecast_data['properties']['updated']
            elevation = forecast_data['properties']['elevation']['value']

            conditions = []
            time_periods = []
            temp_f = []
            humidity = []
            wind_speed = []
            for i in range(0, 13):
                time_periods.append(
                    forecast_data['properties']['periods'][i]['name'])
                conditions.append(
                    forecast_data['properties']['periods'][i]['shortForecast'])
                temp_f.append(
                    forecast_data['properties']['periods'][i]['temperature'])
                humidity.append(
                    forecast_data['properties']['periods'][i]['relativeHumidity']['value'])
                wind_speed.append(forecast_data['properties']['periods'][i]['windDirection'] +
                                  " " + forecast_data['properties']['periods'][i]['windSpeed'])

            # Package weather data into lists
            weather_data = [location, time_stamp, time_periods,
                            conditions, temp_f, humidity, wind_speed]
            location_data = [location, longitude, latitude, elevation]

            return weather_data, location_data, latitude, longitude

        else:
            print(f"Error: {forecast_response.status_code}")
    else:
        # If the request was not successful, print the error code
        print(f"Error: {response.status_code}")
