import sqlite3
import hashlib
from datetime import datetime, date

DB_NAME = "zaraflow.db"

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabel Akun Pengguna
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Tabel Session Login Aktif
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session (
            id INTEGER PRIMARY KEY,
            active_user_id INTEGER,
            FOREIGN KEY (active_user_id) REFERENCES users (id)
        )
    """)
    
    # 3. Tabel Profil Siklus per User
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            last_period_date TEXT NOT NULL,
            cycle_length INTEGER DEFAULT 28,
            period_duration INTEGER DEFAULT 5,
            water_target INTEGER DEFAULT 8,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # 4. Tabel Log Harian per User
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            flow TEXT DEFAULT 'Tidak Ada',
            mood TEXT DEFAULT 'Stabil',
            symptoms TEXT DEFAULT 'Nihil',
            water_intake INTEGER DEFAULT 0,
            UNIQUE(user_id, log_date),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # 5. Tabel Riwayat Siklus Lampau
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cycle_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_date TEXT NOT NULL,
            cycle_length INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()

def register_user(fullname, email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        pw_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
            (fullname, email.lower().strip(), pw_hash)
        )
        user_id = cursor.lastrowid
        today_str = date.today().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO user_profile (user_id, last_period_date, cycle_length, period_duration, water_target) VALUES (?, ?, 28, 5, 8)",
            (user_id, today_str)
        )
        # Sampel arsip siklus lampau agar analitik tidak kosong
        cursor.execute("INSERT INTO cycle_history (user_id, start_date, cycle_length, duration) VALUES (?, '2026-07-20', 28, 5)", (user_id,))
        cursor.execute("INSERT INTO cycle_history (user_id, start_date, cycle_length, duration) VALUES (?, '2026-08-17', 29, 5)", (user_id,))
        conn.commit()
        conn.close()
        return True, "Registrasi berhasil! Silakan masuk."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Email sudah digunakan."

def authenticate_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    cursor.execute("SELECT id, fullname FROM users WHERE email = ? AND password = ?", (email.lower().strip(), pw_hash))
    user = cursor.fetchone()
    conn.close()
    return user

def set_active_session(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO session (id, active_user_id) VALUES (1, ?)", (user_id,))
    conn.commit()
    conn.close()

def get_active_session():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT active_user_id FROM session WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def clear_session():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session WHERE id = 1")
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT fullname, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT last_period_date, cycle_length, period_duration, water_target FROM user_profile WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_profile(user_id, last_date, cycle_len, period_dur, target_water=8):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_profile SET last_period_date = ?, cycle_length = ?, period_duration = ?, water_target = ? WHERE user_id = ?",
        (last_date, cycle_len, period_dur, target_water, user_id)
    )
    conn.commit()
    conn.close()

def get_daily_log(user_id, date_str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT flow, mood, symptoms, water_intake FROM daily_logs WHERE user_id = ? AND log_date = ?", (user_id, date_str))
    row = cursor.fetchone()
    conn.close()
    return row

def update_daily_log(user_id, date_str, flow, mood, symptoms, water):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO daily_logs (user_id, log_date, flow, mood, symptoms, water_intake)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, log_date) DO UPDATE SET
            flow = excluded.flow,
            mood = excluded.mood,
            symptoms = excluded.symptoms,
            water_intake = excluded.water_intake
    """, (user_id, date_str, flow, mood, symptoms, water))
    conn.commit()
    conn.close()

def get_recent_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT start_date, cycle_length, duration FROM cycle_history WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_logs_for_export(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT log_date, flow, mood, symptoms, water_intake FROM daily_logs WHERE user_id = ? ORDER BY log_date DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()

def update_user_name(user_id, new_fullname):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET fullname = ? WHERE id = ?", (new_fullname.strip(), user_id))
    conn.commit()
    conn.close()