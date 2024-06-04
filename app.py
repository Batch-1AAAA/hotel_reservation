from flask import Flask, render_template, request, redirect, url_for, session
from collections import deque
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load users data
if os.path.exists('users.json'):
    with open('users.json') as f:
        users = json.load(f)
else:
    users = {
        "admin": {
            "username": "admin",
            "password": "admin123"
        },
        "customers": []
    }

# Queue to store reservation requests
reservation_queue = deque()

# Maximum number of tables
MAX_TABLES = 10

# List to keep track of reserved tables
reserved_tables = []

@app.route('/')
def index():
    if 'username' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('customer'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if role == 'admin' and username == users['admin']['username'] and password == users['admin']['password']:
            session['username'] = username
            session['role'] = 'admin'
            return redirect(url_for('admin'))
        else:
            for customer in users['customers']:
                if username == customer['username'] and password == customer['password']:
                    session['username'] = username
                    session['role'] = 'customer'
                    return redirect(url_for('customer'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        for customer in users['customers']:
            if customer['username'] == username:
                return 'Username already exists'

        users['customers'].append({'username': username, 'password': password})

        with open('users.json', 'w') as f:
            json.dump(users, f)

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'username' in session and session['role'] == 'admin':
        return render_template('admin.html', reservation_queue=reservation_queue, reserved_tables=reserved_tables)
    return redirect(url_for('login'))

@app.route('/customer')
def customer():
    if 'username' in session and session['role'] == 'customer':
        customer_reservations = [res for res in reserved_tables if res['name'] == session['username']]
        return render_template('customer.html', customer_reservations=customer_reservations)
    return redirect(url_for('login'))

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if 'username' in session and session['role'] == 'customer':
        if request.method == 'POST':
            name = session['username']
            party_size = int(request.form['party_size'])
            reservation_queue.append({'name': name, 'party_size': party_size})
            return redirect(url_for('customer'))
        return render_template('reserve.html')
    return redirect(url_for('login'))

@app.route('/process_reservation')
def process_reservation():
    if 'username' in session and session['role'] == 'admin':
        if reservation_queue and len(reserved_tables) < MAX_TABLES:
            next_reservation = reservation_queue.popleft()
            reserved_tables.append(next_reservation)
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

@app.route('/clear_reservations')
def clear_reservations():
    if 'username' in session and session['role'] == 'admin':
        global reserved_tables
        reserved_tables = []
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
