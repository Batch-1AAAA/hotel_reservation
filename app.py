from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import secrets
import string

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


class Node:
    def __init__(self, data=None):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        last_node = self.head
        while last_node.next:
            last_node = last_node.next
        last_node.next = new_node
    
    def pop(self):
        if not self.head:
            return None
        if not self.head.next:
            popped_node = self.head
            self.head = None
            return popped_node.data
        second_last = self.head
        while second_last.next.next:
            second_last = second_last.next
        popped_node = second_last.next
        second_last.next = None
        return popped_node.data
    
    def remove(self, data):
        head = self.head
        if head is not None:
            if head.data == data:
                self.head = head.next
                head = None
                return
        while head is not None:
            if head.data == data:
                break
            prev = head
            head = head.next
        if head == None:
            return
        prev.next = head.next
        head = None
    
    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next
    
    def clear(self):
        self.head = None

# LinkedList to store reservation requests
reservation_queue = LinkedList()

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

        if role == 'admin':
            if username == users['admin']['username'] and password == users['admin']['password']:
                session['username'] = username
                session['role'] = 'admin'
                return redirect(url_for('admin'))
            else:
                return 'Invalid credentials'
        elif role == 'customer':
            for customer in users['customers']:
                if username == customer['username'] and password == customer['password']:
                    session['username'] = username
                    session['role'] = 'customer'
                    return redirect(url_for('customer'))
            return 'Invalid credentials'
        else:
            return 'Invalid role'
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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global reserved_tables, reservation_queue
    if 'username' in session and session['role'] == 'admin':
        if request.method == 'POST':
            action = request.form.get('action')
            reservation_id = request.form.get('reservation_id')

            if action == 'accept':
                reservation = next((res for res in reservation_queue if res['reservation_id'] == reservation_id), None)
                if reservation:
                    reservation['status'] = 'Reserved'
                    reserved_tables.append(reservation)
                    reservation_queue.remove(reservation)
                    flash('Reservation accepted!', 'success')
                else:
                    flash('Reservation not found!', 'error')

            elif action == 'decline':
                reservation = next((res for res in reservation_queue if res['reservation_id'] == reservation_id), None)
                if reservation:
                    reservation['status'] = 'Pending'
                    reservation_queue.remove(reservation)
                    flash('Reservation declined!', 'success')
                else:
                    flash('Reservation not found!', 'error')

            elif action == 'remove':
                reservation = next((res for res in reserved_tables if res['reservation_id'] == reservation_id), None)
                if reservation:
                    reserved_tables.remove(reservation)
                    flash('Reservation removed!', 'success')
                else:
                    flash('Reservation not found!', 'error')

            elif action == 'process_next':
                if reservation_queue.head:
                    reservation = reservation_queue.pop()
                    reservation['status'] = 'Reserved'
                    reserved_tables.append(reservation)
                    flash('Next reservation processed!', 'success')
                else:
                    flash('No reservations in the queue!', 'error')

            elif action == 'clear_reservations':
                reserved_tables = []
                for reservation in reservation_queue:
                    reservation['status'] = 'Reservation Not found'
                flash('All reservations cleared!', 'success')

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
            phone = session['username']
            party_size = int(request.form['party_size'])
            email_id = session['username']
            special_comments = session['username']

            # Generate a unique ID
            reservation_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

            reservation_queue.append({'reservation_id': reservation_id, 'name': name, 'party_size': party_size, 'phone': phone, 'email_id': email_id, 'special_comments': special_comments})
            flash(f'Reservation successful! Your reservation ID is: {reservation_id}', 'success')  # Customer flash message
            return redirect(url_for('reserve'))
        return render_template('reserve.html')
    return redirect(url_for('login'))

@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if 'username' in session and session['role'] == 'customer':
        if request.method == 'POST':
            reservation_id = request.form.get('reservation_id')
            reservation = next((res for res in reserved_tables if res['reservation_id'] == reservation_id), None)
            if reservation:
                flash('Reservation found!', 'reservation_status_success')
                return render_template('check_status.html', reservation=reservation)
            else:
                reservation = next((res for res in reservation_queue if res['reservation_id'] == reservation_id), None)
                if reservation:
                    flash('Reservation is pending!', 'reservation_status_pending')
                    reservation['status'] = 'Pending'
                    return render_template('check_status.html', reservation=reservation, status='Pending')
                flash('Reservation not found. Please enter a valid ID.', 'reservation_status_error')
                return render_template('check_status.html')  # Render template without redirect
            
        return render_template('check_status.html')  # Render template without flash messages
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
