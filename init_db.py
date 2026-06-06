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

c.execute('''CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY,
    name TEXT,
    gender TEXT,
    department TEXT,
    role TEXT,
    address TEXT,
    lga TEXT,
    email TEXT,
    date_added TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS trainings (
    id INTEGER PRIMARY KEY,
    training_name TEXT UNIQUE,
    description TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS user_trainings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    training_id INTEGER,
    completion_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(training_id) REFERENCES trainings(id)
)''')

# Insert default trainings
default_trainings = [
    ("Foundation School", "Basic Christian Foundation"),
    ("Pastoral Training", "Leadership & Ministry Training"),
    ("Bible Study Methods", "How to Study the Bible"),
    ("Prayer & Intercession", "Advanced Prayer Training")
]

for name, desc in default_trainings:
    c.execute("INSERT OR IGNORE INTO trainings (training_name, description) VALUES (?, ?)", (name, desc))

c.execute('''CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    service_id INTEGER,
    timestamp TEXT
)''')

print("✅ Database initialized successfully!")
conn.commit()
conn.close()