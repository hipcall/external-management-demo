import sqlite3

def init_db():
    conn = sqlite3.connect('/root/user_management_system/database.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        address TEXT,
        pin_code TEXT,
        phone TEXT,
        company_name TEXT,
        company_address TEXT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    ''')
    
    # Check if admin exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('''
        INSERT INTO users (first_name, last_name, username, password, role)
        VALUES (?, ?, ?, ?, ?)
        ''', ('Admin', 'User', 'admin', 'admin', 'admin'))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
