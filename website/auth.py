"""
auth.py - Authentication Blueprint

This module defines the authentication blueprint for the Weather Flask app. It includes routes for user login, sign-up,
account management, and logout.

Author: Matthew Lucia
Date: January 23, 2024

"""

from flask import Blueprint, render_template, request, flash, session, redirect, url_for
import re
import sqlite3
import secrets
import hashlib

# Creating a Blueprint named 'auth'
auth = Blueprint('auth', __name__)

# Database filename
DATABASE = 'weather.db'


# Function to generate a random salt
def generate_salt():
    return secrets.token_hex(16)


# Function to hash the password using a given salt
def hash_password(password, salt):
    combined = password + salt
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


# Login route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in
    user = session.get('user')
    if user:
        # Extract user information for rendering
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        curr_user = f"{first_name} {last_name}"
        return render_template("login.html", curr_user=curr_user)
    elif request.method == 'POST':
        # Retrieve user credentials from the form
        email = request.form.get('email')
        password = request.form.get('password')

        # Connect to the database
        conn = sqlite3.connect("weather.db")
        cur = conn.cursor()

        # Retrieve user information from the database based on the email
        user = cur.execute(
            '''SELECT * FROM users WHERE email = ?''', (email,)).fetchone()

        # Check if the user exists
        if not user:
            flash("Email not on record.", category="error")
            return redirect(url_for('auth.login'))

        # Verify the password using the stored salt
        user_salt = user[3]
        user_hashed_input = hash_password(password, user_salt)

        # Check if the entered password matches the stored hash
        if user_hashed_input != user[2]:
            flash("Email and password do not match.", category="error")
        else:
            # Set user information in the session and redirect to the home page
            flash("Login successful.", category="success")
            session['user'] = {
                'user_id': user[0],
                'email': user[1],
                'first_name': user[4],
                'last_name': user[5],
                'city': user[6],
                'state': user[7],
                'preferences': user[8]
            }
            cur.close()
            conn.close()
            return redirect(url_for('views.home'))
        cur.close()
        conn.close()
    return render_template("login.html")


# Sign-up route
@auth.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    # Check if the user is already logged in
    user = session.get('user')
    if user:
        # Extract user information for rendering
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        curr_user = f"{first_name} {last_name}"
        return render_template("login.html", curr_user=curr_user)
    elif request.method == 'POST':
        # Retrieve user information from the sign-up form
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        city = request.form.get('city')
        state = request.form.get('state')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Validation checks for form fields
        if not email or not first_name or not last_name or not city or not state or not password1 or not password2:
            flash('Error. One or more fields left blank.', category='error')
            return redirect(url_for('auth.sign-up'))

        # Validate email format
        if not bool(re.match(r'^\S+@\S+\.\S+$', email)):
            flash("Email not in correct format.", category="error")
            return render_template('sign_up.html')

        # Validate first name
        if not first_name.isalpha():
            flash("First name cannot be empty and must consist of only uppercase and lowercase letters.", category="error")
            return render_template('sign_up.html')

        # Validate last name
        if not last_name.isalpha():
            flash("Last name cannot be empty and must consist of only uppercase and lowercase letters.", category="error")
            return render_template('sign_up.html')

        # Validate password format
        if not bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,16}$', password1)):
            flash("Password must be between 8-16 characters, must contain at least one uppercase letter (A-Z), at least one lowercase letter (a-z), and at least one digit (0-9)", category="error")
            return render_template('sign_up.html')

        # Check if passwords match
        if password1 != password2:
            flash("Passwords do not match.", category="error")
            return render_template('sign_up.html')
        else:
            # Connect to the database
            conn = sqlite3.connect(DATABASE)
            cur = conn.cursor()

            # Check if the email is already registered
            user_chk = cur.execute(
                '''SELECT * FROM users WHERE email = ?''', (email,)).fetchone()
            if user_chk:
                flash("Email has already been registered.", category="error")
            else:
                # Generate a salt and hash the password
                salt = generate_salt()
                hashed_password = hash_password(password1, salt)
                user_data = [email, hashed_password, salt,
                             first_name, last_name, city, state]

                # Insert user data into the database
                cur.execute(
                    '''INSERT INTO users (email, hashed_password, salt, first_name, last_name, city, state) VALUES (?, ?, ?, ?, ?, ?, ?)''', user_data)
                conn.commit()
                cur.close()
                conn.close()
                flash("Registration successful", category="success")
                return render_template("login.html")

            cur.close()
            conn.close()
    return render_template("sign_up.html")


# Logout route
@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('views.home'))


# Account route
@auth.route("/account", methods=['GET', 'POST'])
def account():
    if request.method == 'GET':
        # Retrieve user information from the session
        user = session.get('user', '')
        return render_template('account.html', user=user)


# Update account route
@auth.route('/update_account', methods=['POST'])
def update_account():
    if request.method == 'POST':
        # Retrieve updated user information from the form
        newEmail = request.form.get('newEmail', '')
        newFirstName = request.form.get('newFirstName', '')
        newLastName = request.form.get('newLastName', '')
        newCity = request.form.get('newCity', '')
        newState = request.form.get('newState', '')
        newPreferences = request.form.get('newPreferences', '') # TODO emails

        # Connect to the database
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()

        # Retrieve user ID from the session
        user_id = session['user']['user_id']

        try:
            # Update user information in the database
            if newEmail:
                cur.execute(
                    'UPDATE users SET email = ? WHERE user_id = ?', (newEmail, user_id,))
                session['user']['email'] = newEmail
            elif newFirstName:
                cur.execute(
                    'UPDATE users SET first_name = ? WHERE user_id = ?', (newFirstName, user_id,))
                session['user']['first_name'] = newFirstName
            elif newLastName:
                cur.execute(
                    'UPDATE users SET last_name = ? WHERE user_id = ?', (newLastName, user_id,))
                session['user']['last_name'] = newLastName
            elif newCity:
                cur.execute(
                    'UPDATE users SET city = ? WHERE user_id = ?', (newCity, user_id,))
                session['user']['city'] = newCity
            elif newState:
                cur.execute(
                    'UPDATE users SET state = ? WHERE user_id = ?', (newState, user_id,))
                session['user']['state'] = newState
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            cur.close()
            conn.close()
            flash('Error updating account.', category="error")
            return redirect(url_for('views.home'))
        flash('Account updated.', category='success')
        return redirect(url_for('views.home'))


# Delete account route
@auth.route('/delete_account')
def delete_account():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    user_id = session['user']['user_id']

    try:
        # Delete user account from the database
        cur.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        conn.commit()
    except Exception:
        flash('Error deleting account.', category='error')
        return redirect(url_for('auth.login'))

    flash('Account successfully deleted', category='success')
    return render_template('home.html')
