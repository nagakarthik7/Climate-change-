from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# User database (you may replace this with a proper database)
users = {
    'user1': {
        'username': 'user1',
        'password': generate_password_hash('password1')
    },
    'user2': {
        'username': 'user2',
        'password': generate_password_hash('password2')
    }
}
def load_user_data():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as file:
            return json.load(file)
    else:
        return {}

# Save user data to a JSON file
def save_user_data(users):
    with open('users.json', 'w') as file:
        json.dump(users, file)


# Function to retrieve weather data
def get_weather_data():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "rain", "showers",
                   "snowfall", "visibility", "evapotranspiration", "wind_direction_10m", "soil_temperature_0cm",
                   "soil_moisture_0_to_1cm"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(2).ValuesAsNumpy()
    hourly_rain = hourly.Variables(3).ValuesAsNumpy()
    hourly_showers = hourly.Variables(4).ValuesAsNumpy()
    hourly_snowfall = hourly.Variables(5).ValuesAsNumpy()
    hourly_visibility = hourly.Variables(6).ValuesAsNumpy()
    hourly_evapotranspiration = hourly.Variables(7).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(8).ValuesAsNumpy()
    hourly_soil_temperature_0cm = hourly.Variables(9).ValuesAsNumpy()
    hourly_soil_moisture_0_to_1cm = hourly.Variables(10).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["rain"] = hourly_rain
    hourly_data["showers"] = hourly_showers
    hourly_data["snowfall"] = hourly_snowfall
    hourly_data["visibility"] = hourly_visibility
    hourly_data["evapotranspiration"] = hourly_evapotranspiration
    hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
    hourly_data["soil_temperature_0cm"] = hourly_soil_temperature_0cm
    hourly_data["soil_moisture_0_to_1cm"] = hourly_soil_moisture_0_to_1cm

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    # Calculate the average of each attribute
    averages = hourly_dataframe.mean()

    averages_dict = averages.to_dict()

    return averages_dict



def get_Admin_weather_data(latitude, longitude):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "rain", "showers",
                   "snowfall", "visibility", "evapotranspiration", "wind_direction_10m", "soil_temperature_0cm",
                   "soil_moisture_0_to_1cm"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()

    # Convert data to a dictionary
    weather_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
        "precipitation_probability": hourly.Variables(2).ValuesAsNumpy(),
        "rain": hourly.Variables(3).ValuesAsNumpy(),
        "showers": hourly.Variables(4).ValuesAsNumpy(),
        "snowfall": hourly.Variables(5).ValuesAsNumpy(),
        "visibility": hourly.Variables(6).ValuesAsNumpy(),
        "evapotranspiration": hourly.Variables(7).ValuesAsNumpy(),
        "wind_direction_10m": hourly.Variables(8).ValuesAsNumpy(),
        "soil_temperature_0cm": hourly.Variables(9).ValuesAsNumpy(),
        "soil_moisture_0_to_1cm": hourly.Variables(10).ValuesAsNumpy()
    }

    return weather_data


# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Load user data
        users = load_user_data()
        if username in users:
            return 'Username already exists!'
        users[username] = {'username': username, 'password': generate_password_hash(password), 'role': 'user'}
        # Save user data
        save_user_data(users)
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_user_data()
        if username not in users or not check_password_hash(users[username]['password'], password):
            return 'Invalid username or password!'
        session['logged_in'] = True
        session['username'] = username
        session['role'] = users[username]['role']
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session and session['logged_in']:
        # Get weather data
        weather_info = get_weather_data()
        return render_template('dashboard.html', weather_info=weather_info)
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'logged_in' in session and session['logged_in'] and session['role'] == 'admin':
        # Get weather data for the admin dashboard
        latitude = 52.52
        longitude = 13.41
        weather_info = get_Admin_weather_data(latitude, longitude)
        return render_template('policyDashboard.html', weather_info=weather_info, enumerate=enumerate)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
