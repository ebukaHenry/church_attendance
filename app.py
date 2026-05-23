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

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    # For local development only
    app.run(host='0.0.0.0', port=5000, debug=True)