from flask import Flask, request, jsonify, render_template, url_for, Response
from flask_cors import CORS
import sqlite3
import os
import json
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

DB_PATH = os.environ.get('DB_PATH', '/app/data/database.db')

# --- AUTHENTICATION ---

def check_auth(username, password):
    """Kullanıcı adı ve şifreyi kontrol eder."""
    return username == 'admin' and password == 'admin123'

def authenticate():
    """401 Unauthorized yanıtı döndürür."""
    return Response(
        'Kimlik doğrulama gerekli.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_phone(phone):
    if not phone:
        return phone
    phone = phone.strip()
    if phone.startswith('+90'):
        phone = phone[3:]
    elif phone.startswith('90') and len(phone) == 12:
        phone = phone[2:]
    elif phone.startswith('0') and len(phone) == 11:
        phone = phone[1:]
    return phone

# --- USER MANAGEMENT APIs ---

@app.route('/api/users', methods=['GET'])
@requires_auth
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, first_name, last_name, phone, pin_code, role FROM users').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/users', methods=['POST'])
@requires_auth
def add_user():
    data = request.json
    conn = get_db_connection()
    phone = normalize_phone(data.get('phone'))
    conn.execute("""INSERT INTO users (first_name, last_name, phone, pin_code, role) 
                    VALUES (?, ?, ?, ?, ?)""", 
                 (data.get('first_name'), data.get('last_name'), phone, data.get('pin_code'), data.get('role', 'user')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@requires_auth
def update_user(user_id):
    data = request.json
    conn = get_db_connection()
    phone = normalize_phone(data.get('phone'))
    conn.execute("""UPDATE users SET first_name=?, last_name=?, phone=?, pin_code=?, role=? 
                    WHERE id=?""", 
                 (data.get('first_name'), data.get('last_name'), phone, data.get('pin_code'), data.get('role'), user_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@requires_auth
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# --- SETTINGS APIs ---

@app.route('/api/settings/active-dial', methods=['GET'])
@requires_auth
def get_active_dial():
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = 'active_dial_number'").fetchone()
    conn.close()
    return jsonify({'phone': row['value'] if row else None})

@app.route('/api/settings/active-dial', methods=['POST'])
@requires_auth
def set_active_dial():
    data = request.json
    phone = data.get('phone')
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_dial_number', ?)", (phone,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/settings/active-extension', methods=['GET'])
@requires_auth
def get_active_extension():
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = 'active_extension'").fetchone()
    conn.close()
    return jsonify({'extension': row['value'] if row else None})

@app.route('/api/settings/active-extension', methods=['POST'])
@requires_auth
def set_active_extension():
    data = request.json
    extension = data.get('extension')
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_extension', ?)", (extension,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# --- LOGGING ---

@app.after_request
def log_request_response(response):
    # Sadece Hipcall Ingress isteklerini logla
    if request.path == '/api/external/hipcall-ingress':
        try:
            req_body = request.get_data(as_text=True)
            res_body = response.get_data(as_text=True)
            
            # JSON Validate kontrolü (Body çok büyükse veya binary ise diye)
            if len(req_body) > 5000: req_body = "Body too large"
            if len(res_body) > 5000: res_body = "Body too large"

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO logs (method, path, request_body, response_body) VALUES (?, ?, ?, ?)",
                (request.method, request.path, req_body, res_body)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Logging error: {e}")
            
    return response

@app.route('/api/logs', methods=['GET'])
@requires_auth
def get_logs():
    conn = get_db_connection()
    logs = conn.execute("SELECT id, timestamp, method, path, request_body, response_body FROM logs ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify([dict(l) for l in logs])

@app.route('/api/logs', methods=['DELETE'])
@requires_auth
def delete_logs():
    conn = get_db_connection()
    conn.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# --- HIPCALL EXTERNAL MANAGEMENT INGRESS ---

@app.route('/api/external/hipcall-ingress', methods=['POST'])
def hipcall_ingress():
    data = request.json
    caller = data.get('caller')
    gather_data = data.get('data', {})

    conn = get_db_connection()
    normalized_caller = normalize_phone(caller)
    user = conn.execute(
        'SELECT * FROM users WHERE phone = ?', 
        (normalized_caller,)
    ).fetchone()

    # User yoksa direkt hata
    if not user:
        conn.close()
        return jsonify({
            "version": "1",
            "seq": [
                {
                    "action": "play",
                    "args": {
                        "url": url_for('static', filename='audio/error_1.mp3', _external=True)
                    }
                },
                {"action": "hangup"}
            ]
        })

    # Ana menü seçimi kontrolü
    main_menu_choice = gather_data.get('main_menu_choice')

    if not main_menu_choice:
        conn.close()
        return jsonify({
            "version": "1",
            "seq": [
                {
                    "action": "gather",
                    "args": {
                        "min_digits": 1,
                        "max_digits": 1,
                        "ask": url_for('static', filename='audio/karsilama.mp3', _external=True),
                        "variable_name": "main_menu_choice"
                    }
                }
            ]
        })

    # Seçim 1: PIN sorma ve doğrulama
    if main_menu_choice == '1':
        entered_pin = gather_data.get('new_pin_code')
        
        if not entered_pin:
            conn.close()
            return jsonify({
                "version": "1",
                "seq": [
                    {
                        "action": "gather",
                        "args": {
                            "min_digits": 1,
                            "max_digits": 4,
                            "ask": url_for('static', filename='audio/ask_pin_1.mp3', _external=True),
                            "variable_name": "new_pin_code"
                        }
                    }
                ]
            })
        
        if entered_pin == user['pin_code']:
            conn.close()
            return jsonify({
                "version": "1",
                "seq": [
                    {
                        "action": "play",
                        "args": {
                            "url": url_for('static', filename='audio/pin_basari.mp3', _external=True)
                        }
                    },
                    {"action": "hangup"}
                ]
            })
        else:
            conn.close()
            return jsonify({
                "version": "1",
                "seq": [
                    {
                        "action": "play",
                        "args": {
                            "url": url_for('static', filename='audio/error.mp3', _external=True)
                        }
                    },
                    {"action": "hangup"}
                ]
            })

    # Seçim 2: Dial (Dış Hat)
    elif main_menu_choice == '2':
        active_row = conn.execute("SELECT value FROM settings WHERE key = 'active_dial_number'").fetchone()
        destination = active_row['value'] if active_row else "905060508169" # Fallback
        conn.close()
        return jsonify({
            "version": "1",
            "seq": [
                {
                    "action": "dial",
                    "args": {
                        "destination": destination
                    }
                }
            ]
        })

    # Seçim 3: Connect (Dahili)
    elif main_menu_choice == '3':
        active_ext_row = conn.execute("SELECT value FROM settings WHERE key = 'active_extension'").fetchone()
        destination = active_ext_row['value'] if active_ext_row else "1090" # Fallback
        conn.close()
        return jsonify({
            "version": "1",
            "seq": [
                {
                    "action": "connect",
                    "args": {
                        "destination": destination
                    }
                }
            ]
        })

    else:
        # Geçersiz seçim
        conn.close()
        return jsonify({
            "version": "1",
            "seq": [
                {
                    "action": "play",
                    "args": {
                        "url": url_for('static', filename='audio/error_1.mp3', _external=True)
                    }
                },
                {"action": "hangup"}
            ]
        })
# --- FRONTEND ROUTE ---

@app.route('/')
@requires_auth
def index():
    return render_template('index.html')

@app.route('/settings')
@requires_auth
def settings():
    return render_template('settings.html')

@app.route('/logs')
@requires_auth
def logs():
    return render_template('logs.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
