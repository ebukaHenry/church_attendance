import sqlite3

conn = sqlite3.connect('church.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT UNIQUE,
    gender TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY,
    service_date TEXT,
    service_type TEXT,
    qr_code TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    service_id INTEGER,
    timestamp TEXT
)''')

print("✅ Database initialized successfully!")
conn.commit()
conn.close()