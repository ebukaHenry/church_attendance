from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import qrcode
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "grace_chapel_secret_2026"

def get_db():
    conn = sqlite3.connect('church.db')
    conn.row_factory = sqlite3.Row
    return conn

# ====================== LOGIN SYSTEM ======================

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Demo login (you can improve later with real users)
        session['logged_in'] = True
        session['username'] = "Pastor/Admin"
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Protect all routes
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please login first!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/generate_qr', methods=['GET', 'POST'])
@login_required
def generate_qr():
    if request.method == 'POST':
        service_date = request.form['service_date']
        service_type = request.form['service_type']
        
        base_url = "https://web-production-7d59a.up.railway.app"
        
        qr_link = f"{base_url}/scan?data=church_service|{service_date}|{service_type}"
        
        conn = get_db()
        qr = qrcode.make(qr_link)
        qr_path = f"static/qr_{service_date}_{service_type}.png"
        qr.save(qr_path)
        
        conn.execute("INSERT INTO services (service_date, service_type, qr_code) VALUES (?, ?, ?)",
                    (service_date, service_type, qr_path))
        conn.commit()
        
        flash('QR Code generated successfully!', 'success')
        return render_template('generate_qr.html', 
                             qr_image=qr_path, 
                             service_date=service_date, 
                             service_type=service_type)
    
    return render_template('generate_qr.html')

@app.route('/scan')
def scan_qr():
    try:
        data = request.args.get('data')
        if not data:
            return "Missing data parameter", 400
            
        if '|' not in data:
            return "Invalid QR format", 400
            
        parts = data.split('|')
        service_date = parts[-2]
        service_type = parts[-1]
        
        return render_template('attendance_form.html', 
                             service_date=service_date, 
                             service_type=service_type)
    except:
        return """
            <h2 style="color:red;text-align:center;margin-top:80px;">
                Invalid QR Code<br><br>
                Please generate a new one.
            </h2>
        """, 400
    
@app.route('/attendance_list')
@login_required
def attendance_list():
    conn = get_db()
    records = conn.execute("""
        SELECT u.name, u.phone, u.gender, s.service_date, s.service_type, a.timestamp
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        JOIN services s ON a.service_id = s.id
        ORDER BY a.timestamp DESC
    """).fetchall()
    return render_template('attendance_list.html', records=records)

@app.route('/all_members')
@login_required
def all_members():
    conn = get_db()
    members = conn.execute("""
        SELECT u.name, u.phone, u.gender, 
               COUNT(a.id) as total_attendance
        FROM users u
        LEFT JOIN attendance a ON u.id = a.user_id
        GROUP BY u.id
        ORDER BY total_attendance DESC
    """).fetchall()
    return render_template('all_members.html', members=members)


@app.route('/workers', methods=['GET', 'POST'])
@login_required
def workers():
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        department = request.form['department']
        role = request.form['role']
        address = request.form['address']
        lga = request.form['lga']
        email = request.form.get('email')
        
        conn.execute("""INSERT INTO workers 
            (name, gender, department, role, address, lga, email, date_added) 
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (name, gender, department, role, address, lga, email))
        conn.commit()
        flash('Worker added successfully!', 'success')
        return redirect(url_for('workers'))
    
    # Get filter
    dept_filter = request.args.get('department', 'all')
    
    query = "SELECT * FROM workers"
    params = []
    if dept_filter != 'all':
        query += " WHERE department = ?"
        params.append(dept_filter)
    query += " ORDER BY department, name"
    
    workers_list = conn.execute(query, params).fetchall()
    
    departments = conn.execute("SELECT DISTINCT department FROM workers ORDER BY department").fetchall()
    
    return render_template('workers.html', 
                         workers=workers_list, 
                         departments=departments,
                         current_filter=dept_filter)
# ====================== PUBLIC WORKERS FORM ======================

@app.route('/join_workers', methods=['GET', 'POST'])
def join_workers():
    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        department = request.form['department']
        role = request.form['role']
        address = request.form['address']
        lga = request.form['lga']
        
        conn = get_db()
        conn.execute("""INSERT INTO workers 
            (name, gender, department, role, address, lga, date_added) 
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (name, gender, department, role, address, lga))
        conn.commit()
        
        return render_template('thank_you_worker.html')
    
    return render_template('public_workers_form.html')


# @app.route('/workers')
# @login_required
# def workers():
#     conn = get_db()
#     workers_list = conn.execute("SELECT * FROM workers ORDER BY department, name").fetchall()
#     return render_template('workers.html', workers=workers_list)

# ====================== TRAINING MANAGEMENT ======================

@app.route('/trainings')
@login_required
def trainings():
    conn = get_db()
    
    # Dashboard stats
    total_members = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    
    training_stats = conn.execute("""
        SELECT t.training_name, COUNT(ut.id) as completed,
               ROUND(COUNT(ut.id) * 100.0 / ?, 1) as percentage
        FROM trainings t
        LEFT JOIN user_trainings ut ON t.id = ut.training_id
        GROUP BY t.id
        ORDER BY completed DESC
    """, (total_members if total_members > 0 else 1,)).fetchall()
    
    # All members with their trainings
    members = conn.execute("""
        SELECT u.id, u.name, u.gender, u.phone,
               GROUP_CONCAT(t.training_name, ', ') as trainings
        FROM users u
        LEFT JOIN user_trainings ut ON u.id = ut.user_id
        LEFT JOIN trainings t ON ut.training_id = t.id
        GROUP BY u.id
        ORDER BY u.name
    """).fetchall()
    
    trainings_list = conn.execute("SELECT * FROM trainings").fetchall()
    
    return render_template('trainings.html', 
                         training_stats=training_stats,
                         members=members,
                         trainings_list=trainings_list,
                         total_members=total_members)

@app.route('/organogram')
@login_required
def organogram():
    conn = get_db()
    hierarchy = conn.execute("""
        SELECT department, role, COUNT(*) as count
        FROM workers 
        GROUP BY department, role
        UNION
        SELECT 'Members' as department, 'Regular Member' as role, COUNT(*) as count
        FROM users
    """).fetchall()
    return render_template('organogram.html', hierarchy=hierarchy)

@app.route('/add_training', methods=['POST'])
@login_required
def add_training():
    user_id = request.form.get('user_id')
    training_id = request.form.get('training_id')
    completion_date = request.form.get('completion_date')
    
    conn = get_db()
    conn.execute("INSERT INTO user_trainings (user_id, training_id, completion_date) VALUES (?, ?, ?)",
                (user_id, training_id, completion_date))
    conn.commit()
    flash('Training record added!', 'success')
    return redirect(url_for('trainings'))

# ====================== MANAGE MVPs ======================

@app.route('/manage_mvps')
@login_required
def manage_mvps():
    conn = get_db()
    mvps = conn.execute("""
        SELECT id, name, phone, gender, 
               (SELECT MIN(timestamp) FROM attendance 
                WHERE user_id = users.id) as first_attendance
        FROM users 
        ORDER BY name
    """).fetchall()
    return render_template('manage_mvps.html', mvps=mvps)


@app.route('/add_mvp', methods=['POST'])
@login_required
def add_mvp():
    name = request.form.get('name')
    phone = request.form.get('phone')
    gender = request.form.get('gender')
    
    if not name or not phone or not gender:
        flash('All fields are required!', 'danger')
        return redirect(url_for('manage_mvps'))
    
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (name, phone, gender) VALUES (?, ?, ?)",
                    (name.strip(), phone.strip(), gender))
        conn.commit()
        flash('✅ New MVP added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('❌ Phone number already exists!', 'danger')
    except Exception as e:
        flash('Error adding MVP', 'danger')
    
    return redirect(url_for('manage_mvps'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    # For local development only
    app.run(host='0.0.0.0', port=5000, debug=True)