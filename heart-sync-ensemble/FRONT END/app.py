from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3,joblib
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  phone TEXT NOT NULL)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')

        if not all([name, email, username, password, confirm_password, phone]):
            flash('All fields are required!')
            return redirect(url_for('register'))

        name_regex = r'^[a-zA-Z\s]{2,}$'
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        username_regex = r'^[a-zA-Z0-9]{3,20}$'
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        phone_regex = r'^\d{10}$'

        if not re.match(name_regex, name):
            flash('Name must be at least 2 characters long and contain only letters and spaces.')
            return redirect(url_for('register'))
        if not re.match(email_regex, email):
            flash('Invalid email address.')
            return redirect(url_for('register'))
        if not re.match(username_regex, username):
            flash('Username must be 3-20 characters long and alphanumeric.')
            return redirect(url_for('register'))
        if not re.match(password_regex, password):
            flash('Password must be at least 8 characters, with one uppercase, one lowercase, one number, and one special character.')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))
        if not re.match(phone_regex, phone):
            flash('Phone number must be exactly 10 digits.')
            return redirect(url_for('register'))

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, username, password, phone) VALUES (?, ?, ?, ?, ?)",
                      (name, email, username, password, phone))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!')
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        username_regex = r'^[a-zA-Z0-9]{3,20}$'
        if not username or not password:
            flash('Username and password are required!')
            return redirect(url_for('login'))
        if not re.match(username_regex, username):
            flash('Username must be 3-20 characters long and alphanumeric.')
            return redirect(url_for('login'))

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and user[0] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/home')
def home():
    # if 'username' in session:
    return render_template('home.html')
    # return redirect(url_for('login'))

from flask import request, flash, redirect, url_for, render_template
import joblib
import numpy as np
import pandas as pd

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            # Retrieve form data
            input_data = {
                'age': int(request.form['age']),
                'sex': int(request.form['sex']),
                'cp': int(request.form['cp']),
                'trestbps': int(request.form['trestbps']),
                'chol': int(request.form['chol']),
                'fbs': int(request.form['fbs']),
                'restecg': int(request.form['restecg']),  # ✅ added
                'thalach': int(request.form['thalach']),
                'exang': int(request.form['exang']),
                'oldpeak': float(request.form['oldpeak']),
                'slope': int(request.form['slope']),
                'ca': int(request.form['ca']),
                'thal': int(request.form['thal'])
            }

            # Load feature order
            feature_names = joblib.load("models/feature_names.joblib")

            # Arrange input in correct order
            input_df = pd.DataFrame([[input_data[feat] for feat in feature_names]], columns=feature_names)

            # Load preprocessor and model
            scaler = joblib.load("models/scaler.joblib")
            kbest = joblib.load("models/kbest.joblib")
            model = joblib.load("models/Voting Classifier.joblib")

            # Apply transformation
            input_scaled = scaler.transform(input_df)
            input_kbest = kbest.transform(input_scaled)

            # Predict
            prediction = model.predict(input_kbest)[0]
            proba = model.predict_proba(input_kbest)[0][1]

            result = "No Heart Disease" if prediction == 0 else "Heart Disease"
            flash(f'Prediction: {result} (Probability: {proba:.2f})', 'success')
            return render_template('prediction.html', result=result)

        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('predict'))

    return render_template('prediction.html', result=None)



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)