from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_mail import Mail, Message
from collections import deque
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['MAIL_SERVER'] = 'gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'messnair1@gmail.com'
app.config['MAIL_PASSWORD'] = 'NairMess@2024'
mail = Mail(app)
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
        reservation = session.get('next_reservation')
        return render_template('admin.html', reservation_queue=reservation_queue, reserved_tables=reserved_tables, reservation=reservation)
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
            phone= session['username']
            party_size = int(request.form['party_size'])
            email_id=session['username']
            special_comments=session['username']
            reservation_queue.append({'name': name, 'party_size': party_size,'phone':phone,'email_id':email_id,'special_comments':special_comments})
            flash('Reservation successful!', 'success')
            return redirect(url_for('reserve'))
        return render_template('reserve.html')
    return redirect(url_for('login'))

@app.route('/process_reservation')
def process_reservation():
    if 'username' in session and session['role'] == 'admin':
        if reservation_queue and len(reserved_tables) < MAX_TABLES:
            next_reservation = reservation_queue.popleft()
            session['next_reservation'] = next_reservation
            return redirect(url_for('admin'))
        flash('No reservations to process or all tables are reserved.', 'info')
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

@app.route('/reservation_action', methods=['POST'])
def reservation_action():
    if 'username' in session and session['role'] == 'admin':
        reservation = session.get('next_reservation')
        if request.method == 'POST':
            action = request.form['action']
            if action == 'accept':
                reserved_tables.append(reservation)
                flash('Reservation accepted and booked!', 'success')
                send_reservation_email(reservation, 'accepted')
            elif action == 'decline':
                flash('Reservation declined!', 'danger')
                send_reservation_email(reservation, 'declined')
            session.pop('next_reservation', None)
            return redirect(url_for('admin'))
    return redirect(url_for('login'))

def send_reservation_email(reservation, status):
    subject = f"Your reservation has been {status}"
    body = f"""
    Dear {reservation['name']},

    Your reservation has been {status}.

    Details:
    Party Size: {reservation['party_size']}
    Phone: {reservation['phone']}
    Email: {reservation['email_id']}
    Special Comments: {reservation['special_comments']}

    Thank you!
    """
    msg = Message(subject, sender='your-email@example.com', recipients=[reservation['email_id']])
    msg.body = body
    mail.send(msg)

@app.route('/clear_reservations')
def clear_reservations():
    if 'username' in session and session['role'] == 'admin':
        global reserved_tables
        reserved_tables = []
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
