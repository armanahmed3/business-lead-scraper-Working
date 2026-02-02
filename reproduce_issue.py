import sqlite3
import os
import hashlib
import time

DB_PATH = os.path.join(os.getcwd(), 'users.db')
print(f"Using DB_PATH: {DB_PATH}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT, active INTEGER DEFAULT 1)''')
    
    # Check if admin exists
    c.execute("SELECT username FROM users WHERE username='admin'")
    if not c.fetchone():
        admin_pass = hash_password("admin")
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                     ("admin", admin_pass, "admin"))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def add_user(username, password, role):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    hashed = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                 (username, hashed, role))
        conn.commit()
        print(f"Added user {username}")
        return True
    except sqlite3.IntegrityError as e:
        print(f"Failed to add user: {e}")
        return False
    finally:
        conn.close()

def get_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, role, active FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

# Test Scenario
print("Initializing DB...")
init_db()
print("Initial users:", get_users())

test_user = f"test_user_{int(time.time())}"
print(f"Adding user {test_user}...")
add_user(test_user, "password123", "user")

print("Users after add:", get_users())

print("Simulating restart (re-init)...")
init_db()
print("Users after restart:", get_users())

# Check if user persists
users = [u[0] for u in get_users()]
if test_user in users:
    print("SUCCESS: User persisted.")
else:
    print("FAILURE: User lost.")
