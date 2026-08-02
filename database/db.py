import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'medilensai.db')


class Database:
    def __init__(self):
        self.db_path = DB_PATH

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                filename TEXT NOT NULL,
                patient_name TEXT DEFAULT 'Unknown',
                patient_age INTEGER DEFAULT 0,
                patient_gender TEXT DEFAULT 'Unknown',
                report_type TEXT DEFAULT 'lab_report',
                upload_date TEXT NOT NULL,
                overall_risk_score REAL DEFAULT 0,
                overall_risk_level TEXT DEFAULT 'Unknown',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS health_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                value REAL,
                unit TEXT,
                risk_level TEXT,
                normal_min REAL,
                normal_max REAL,
                FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                is_dismissed INTEGER DEFAULT 0,
                sms_simulated INTEGER DEFAULT 1,
                FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                display_name TEXT,
                category TEXT,
                recommendation_text TEXT NOT NULL,
                risk_level TEXT,
                FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                mobile_number TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'patient',
                created_at TEXT NOT NULL
            );
        ''')
        conn.commit()

        # Schema migrations for existing SQLite databases
        try:
            cursor.execute("ALTER TABLE reports ADD COLUMN user_id INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE reports ADD COLUMN report_type TEXT DEFAULT 'lab_report'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN mobile_number TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN totp_secret TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile_number) WHERE mobile_number IS NOT NULL")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

    # ─── Authentication & User Management ────────────────────────────────────
    def create_user(self, username, password, role='patient', mobile_number=None):
        from werkzeug.security import generate_password_hash
        conn = self.get_connection()
        cursor = conn.cursor()
        
        clean_user   = username.strip()
        clean_mobile = mobile_number.strip() if mobile_number else None

        if clean_mobile:
            existing_mobile = cursor.execute('SELECT id FROM users WHERE mobile_number = ?', (clean_mobile,)).fetchone()
            if existing_mobile:
                conn.close()
                return False, "This mobile number is already registered with another account."

        existing_user = cursor.execute('SELECT id FROM users WHERE username = ?', (clean_user,)).fetchone()
        if existing_user:
            conn.close()
            return False, "Username already exists."

        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'INSERT INTO users (username, mobile_number, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)',
                (clean_user, clean_mobile, generate_password_hash(password), role, now)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return True, user_id
        except sqlite3.IntegrityError as e:
            conn.close()
            return False, "Account registration failed. Username or mobile number already in use."

    def get_user_report_count(self, user_id):
        conn = self.get_connection()
        count = conn.execute('SELECT COUNT(*) FROM reports WHERE user_id=?', (user_id,)).fetchone()[0]
        conn.close()
        return count

    def get_user_today_report_count(self, user_id):
        conn = self.get_connection()
        today_str = datetime.now().strftime('%Y-%m-%d')
        count = conn.execute(
            'SELECT COUNT(*) FROM reports WHERE user_id=? AND upload_date LIKE ?',
            (user_id, f"{today_str}%")
        ).fetchone()[0]
        conn.close()
        return count

    def get_user_by_mobile(self, mobile_number):
        conn = self.get_connection()
        clean = ''.join(filter(str.isdigit, mobile_number))
        row = conn.execute('SELECT * FROM users WHERE mobile_number = ?', (clean,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_by_username(self, username):
        conn = self.get_connection()
        query = 'SELECT * FROM users WHERE username = ? OR mobile_number = ?'
        clean = username.strip()
        row = conn.execute(query, (clean, clean)).fetchone()
        conn.close()
        return dict(row) if row else None

    def save_user_totp_secret(self, user_id, secret):
        conn = self.get_connection()
        conn.execute('UPDATE users SET totp_secret = ? WHERE id = ?', (secret, user_id))
        conn.commit()
        conn.close()

    def update_user_password_by_identifier(self, identifier, new_password):
        from werkzeug.security import generate_password_hash
        conn = self.get_connection()
        clean = identifier.strip()
        conn.execute('UPDATE users SET password_hash = ? WHERE username = ? OR mobile_number = ?',
                     (generate_password_hash(new_password), clean, clean))
        conn.commit()
        conn.close()
        return True
        conn.close()
        return True

    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def verify_user(self, username_or_mobile, password):
        from werkzeug.security import check_password_hash
        user = self.get_user_by_username(username_or_mobile)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    # ─── Reports ─────────────────────────────────────────────────────────────
    def save_report(self, filename, patient_name, patient_age, patient_gender, filepath=None, user_id=1, report_type='lab_report'):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO reports (user_id, filename, patient_name, patient_age, patient_gender, report_type, upload_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, filename, patient_name, patient_age, patient_gender, report_type,
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id

    def update_report_risk(self, report_id, score, level):
        conn = self.get_connection()
        conn.execute(
            'UPDATE reports SET overall_risk_score=?, overall_risk_level=? WHERE id=?',
            (score, level, report_id)
        )
        conn.commit()
        conn.close()

    def get_report(self, report_id):
        conn = self.get_connection()
        row = conn.execute('SELECT * FROM reports WHERE id=?', (report_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_reports(self, user_id=None):
        conn = self.get_connection()
        if user_id is not None:
            rows = conn.execute('SELECT * FROM reports WHERE user_id=? ORDER BY upload_date DESC', (user_id,)).fetchall()
        else:
            rows = conn.execute('SELECT * FROM reports ORDER BY upload_date DESC').fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_recent_reports(self, limit=5, user_id=None):
        conn = self.get_connection()
        if user_id is not None:
            rows = conn.execute(
                'SELECT * FROM reports WHERE user_id=? ORDER BY upload_date DESC LIMIT ?', (user_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM reports ORDER BY upload_date DESC LIMIT ?', (limit,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_report(self, report_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM reports WHERE id=?', (report_id,))
        conn.commit()
        conn.close()

    # ─── Health Parameters ───────────────────────────────────────────────────
    def save_parameters(self, report_id, risk_results):
        conn = self.get_connection()
        for param in risk_results:
            if param.get('value') is not None:
                conn.execute(
                    '''INSERT INTO health_parameters
                       (report_id, parameter_name, display_name, value, unit, risk_level,
                        normal_min, normal_max)
                       VALUES (?,?,?,?,?,?,?,?)''',
                    (report_id, param['name'], param['display_name'], param['value'],
                     param['unit'], param['risk_level'],
                     param['normal_min'], param['normal_max'])
                )
        conn.commit()
        conn.close()

    def get_parameters(self, report_id):
        conn = self.get_connection()
        rows = conn.execute(
            'SELECT * FROM health_parameters WHERE report_id=?', (report_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Recommendations ─────────────────────────────────────────────────────
    def save_recommendations(self, report_id, recommendations):
        conn = self.get_connection()
        for rec in recommendations:
            conn.execute(
                '''INSERT INTO recommendations
                   (report_id, parameter_name, display_name, category, recommendation_text, risk_level)
                   VALUES (?,?,?,?,?,?)''',
                (report_id, rec['parameter'], rec.get('display_name', ''),
                 rec['category'], rec['text'], rec.get('risk_level', ''))
            )
        conn.commit()
        conn.close()

    def get_recommendations(self, report_id):
        conn = self.get_connection()
        rows = conn.execute(
            'SELECT * FROM recommendations WHERE report_id=?', (report_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Alerts ──────────────────────────────────────────────────────────────
    def save_alert(self, report_id, parameter_name, message, severity):
        conn = self.get_connection()
        conn.execute(
            '''INSERT INTO alerts (report_id, parameter_name, message, severity, timestamp)
               VALUES (?,?,?,?,?)''',
            (report_id, parameter_name, message, severity,
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        conn.close()

    def get_report_alerts(self, report_id):
        conn = self.get_connection()
        rows = conn.execute(
            'SELECT * FROM alerts WHERE report_id=? ORDER BY timestamp DESC', (report_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_alerts(self, user_id=None):
        conn = self.get_connection()
        if user_id is not None:
            rows = conn.execute(
                '''SELECT a.*, r.patient_name FROM alerts a
                   JOIN reports r ON a.report_id = r.id
                   WHERE a.is_dismissed=0 AND r.user_id=?
                   ORDER BY a.timestamp DESC''', (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                '''SELECT a.*, r.patient_name FROM alerts a
                   JOIN reports r ON a.report_id = r.id
                   WHERE a.is_dismissed=0
                   ORDER BY a.timestamp DESC'''
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_unread_alert_count(self, user_id=None):
        conn = self.get_connection()
        if user_id is not None:
            count = conn.execute(
                '''SELECT COUNT(*) FROM alerts a
                   JOIN reports r ON a.report_id = r.id
                   WHERE a.is_read=0 AND a.is_dismissed=0 AND r.user_id=?''', (user_id,)
            ).fetchone()[0]
        else:
            count = conn.execute(
                'SELECT COUNT(*) FROM alerts WHERE is_read=0 AND is_dismissed=0'
            ).fetchone()[0]
        conn.close()
        return count

    def mark_all_alerts_read(self, user_id=None):
        conn = self.get_connection()
        if user_id is not None:
            conn.execute(
                '''UPDATE alerts SET is_read=1 WHERE id IN (
                       SELECT a.id FROM alerts a JOIN reports r ON a.report_id = r.id WHERE r.user_id=?
                   )''', (user_id,)
            )
        else:
            conn.execute('UPDATE alerts SET is_read=1')
        conn.commit()
        conn.close()

    def dismiss_alert(self, alert_id):
        conn = self.get_connection()
        conn.execute('UPDATE alerts SET is_dismissed=1 WHERE id=?', (alert_id,))
        conn.commit()
        conn.close()

    # ─── Stats & Trends ──────────────────────────────────────────────────────
    def get_stats(self, user_id=None):
        conn = self.get_connection()
        if user_id is not None:
            total = conn.execute('SELECT COUNT(*) FROM reports WHERE user_id=?', (user_id,)).fetchone()[0]
            unread = conn.execute(
                '''SELECT COUNT(*) FROM alerts a JOIN reports r ON a.report_id = r.id
                   WHERE a.is_read=0 AND a.is_dismissed=0 AND r.user_id=?''', (user_id,)
            ).fetchone()[0]
            high_risk = conn.execute(
                "SELECT COUNT(*) FROM reports WHERE overall_risk_level IN ('High','Critical') AND user_id=?", (user_id,)
            ).fetchone()[0]
        else:
            total = conn.execute('SELECT COUNT(*) FROM reports').fetchone()[0]
            unread = conn.execute(
                'SELECT COUNT(*) FROM alerts WHERE is_read=0 AND is_dismissed=0'
            ).fetchone()[0]
            high_risk = conn.execute(
                "SELECT COUNT(*) FROM reports WHERE overall_risk_level IN ('High','Critical')"
            ).fetchone()[0]
        conn.close()
        return {'total_reports': total, 'unread_alerts': unread, 'high_risk_count': high_risk}

    def get_health_trends(self, user_id=None):
        conn = self.get_connection()
        if user_id is not None:
            rows = conn.execute(
                '''SELECT r.upload_date, r.patient_name, h.parameter_name, h.display_name,
                          h.value, h.unit, h.risk_level
                   FROM health_parameters h
                   JOIN reports r ON h.report_id = r.id
                   WHERE r.user_id=?
                   ORDER BY r.upload_date ASC''', (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                '''SELECT r.upload_date, r.patient_name, h.parameter_name, h.display_name,
                          h.value, h.unit, h.risk_level
                   FROM health_parameters h
                   JOIN reports r ON h.report_id = r.id
                   ORDER BY r.upload_date ASC'''
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
