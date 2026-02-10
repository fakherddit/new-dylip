import os
import time
import random
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify

# ================= CONFIGURATION =================
DB_URL = "postgresql://dylip_key_user:TwbqpTuAggFaAXhIX7Q7pMmJIih5vEQe@dpg-d5v88bl6ubrc73c8tlqg-a.oregon-postgres.render.com/dylip_key"
ADMIN_SECRET = "super_secret_admin_key_123" 
# =================================================

app = Flask(__name__)

def get_db():
    try:
        conn = psycopg2.connect(DB_URL, sslmode='prefer', connect_timeout=10)
        conn.autocommit = True
        return conn
    except:
        try:
             conn = psycopg2.connect(DB_URL, sslmode='require', connect_timeout=10)
             conn.autocommit = True
             return conn
        except:
             return None

@app.route('/')
@app.route('/health')
def home():
    return jsonify({"status": "ok", "service": "ST FAMILY License Server"})

@app.route('/validate', methods=['POST'])
def validate():
    data = request.get_json(silent=True) or {}
    key = data.get('key')
    hwid = data.get('hwid')

    if not key or not hwid:
        return jsonify({"valid": False, "message": "Missing key or HWID"})

    conn = get_db()
    if not conn:
        return jsonify({"valid": False, "message": "Database Error"}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Validate Key
            cur.execute("""
                SELECT * FROM licenses 
                WHERE license_key = %s AND expiry_date > NOW() AND status = 'active'
            """, (key,))
            
            license_data = cur.fetchone()
            
            if not license_data:
                 return jsonify({"valid": False, "message": "Invalid or Expired Key"})

            # Check HWID logic
            type_ = license_data.get('key_type', 'standard')
            saved_hwid = license_data.get('hwid')
            
            if type_ and str(type_).startswith('global'):
                pass 
            elif not saved_hwid:
                cur.execute("UPDATE licenses SET hwid = %s, last_used = NOW() WHERE license_key = %s", (hwid, key))
            elif saved_hwid != hwid:
                return jsonify({"valid": False, "message": "Key bound to another device"})
            else:
                cur.execute("UPDATE licenses SET last_used = NOW() WHERE license_key = %s", (key,))

            return jsonify({
                "valid": True,
                "message": "Authenticated",
                "expiry_date": str(license_data['expiry_date'])
            })
    except Exception as e:
        return jsonify({"valid": False, "message": str(e)}), 500
    finally:
        if conn:
            conn.close()

# === NEW ADMIN ENDPOINTS FOR LOCAL BOT ===
@app.route('/admin/generate', methods=['POST'])
def admin_generate():
    auth = request.headers.get("X-Admin-Secret")
    if auth != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json()
    days = int(data.get('days', 30))
    count = int(data.get('count', 1))
    
    conn = get_db()
    try:
        keys = []
        with conn.cursor() as cur:
            for _ in range(count):
                key = "{:04X}-{:04X}-{:04X}-{:04X}".format(random.randint(0,0xFFFF), random.randint(0,0xFFFF), random.randint(0,0xFFFF), random.randint(0,0xFFFF))
                cur.execute("INSERT INTO licenses (license_key, expiry_date, key_type) VALUES (%s, NOW() + INTERVAL '%s days', 'standard') RETURNING license_key", (key, days))
                keys.append(key)
        return jsonify({"keys": keys})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
