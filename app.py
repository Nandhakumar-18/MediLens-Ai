import os
import uuid
import html
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash, send_from_directory, Response
from werkzeug.utils import secure_filename

from database.db import Database
from modules.ocr_extractor import OCRExtractor
from modules.risk_predictor import RiskPredictor
from modules.recommendation_engine import RecommendationEngine
from modules.alert_system import AlertSystem
from modules.computer_vision import ComputerVisionAnalyzer
from modules.fhir_exporter import FHIRExporter
from modules.translator import OfflineTranslator
from modules.totp_authenticator import TOTPAuthenticator

from datetime import timedelta

# ─── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'medilensai-offline-2024-secret-key-prod-hash')

# Security & Persistent Device Login (Remember Me for 30 days)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Security: Max Upload Size Limit (16 MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff', 'bmp', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── Security Headers Middleware ──────────────────────────────────────────────
@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:;"
    )
    return response


# ─── Error Handlers ───────────────────────────────────────────────────────────
@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File size exceeds the 16MB limit. Please upload a smaller file.', 'error')
    return redirect(url_for('index'))


# ─── Module instances ─────────────────────────────────────────────────────────
db          = Database()
ocr         = OCRExtractor()
predictor   = RiskPredictor()
recommender = RecommendationEngine()
cv_analyzer = ComputerVisionAnalyzer()
fhir_engine = FHIRExporter()
translator  = OfflineTranslator()
totp_engine = TOTPAuthenticator()


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please sign in to access your personal health reports.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ─── Authentication Routes ───────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in on this device, skip login screen!
    if session.get('user_id') and request.method == 'GET':
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user     = db.verify_user(username, password)
        if user:
            session.permanent = True  # Keep user logged in on this device for 30 days!
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            flash(f"Welcome back, {user['username']}!", 'success')
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        else:
            flash('Invalid username/mobile or password. Please try again.', 'error')
    return render_template('login.html')


@app.route('/request-sms-otp', methods=['POST'])
def request_sms_otp():
    import random
    from datetime import datetime, timedelta
    
    data         = request.get_json() or {}
    mobile_input = data.get('mobile_number', '').strip()
    user         = None
    clean_mobile = ''.join(filter(str.isdigit, mobile_input))
    
    if len(clean_mobile) >= 10:
        user = db.get_user_by_mobile(clean_mobile)
    
    if not user:
        user = db.get_user_by_username(mobile_input)
        if user and user.get('mobile_number'):
            clean_mobile = ''.join(filter(str.isdigit, user['mobile_number']))

    if not user or not clean_mobile or len(clean_mobile) < 10:
        return jsonify({'success': False, 'message': 'No registered account found with a valid 10-digit mobile number for this input.'}), 200

    # Generate 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"
    expiry   = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

    session['reset_otp']    = otp_code
    session['reset_mobile'] = clean_mobile
    session['reset_expiry'] = expiry

    # Log to offline SMS log file
    log_file = os.path.join(app.root_path, 'sms_simulation_log.txt')
    log_entry = (
        f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"[OFFLINE SMS OTP] Recipient: +91 {clean_mobile} | OTP Code: {otp_code} | Expire: 5 min\n"
    )
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    sms_uri = f"sms:+91{clean_mobile}?body=MediLensAI%20Security%20OTP:%20{otp_code}%20(Valid%20for%205%20minutes)"

    return jsonify({
        'success': True,
        'message': f'Offline SMS OTP generated for +91 {clean_mobile}.',
        'otp': otp_code,
        'mobile': clean_mobile,
        'sms_uri': sms_uri
    })


@app.route('/verify-sms-otp', methods=['POST'])
def verify_sms_otp():
    from datetime import datetime
    
    data          = request.get_json() or {}
    mobile_input  = data.get('mobile_number', '').strip()
    otp_input     = data.get('otp_code', '').strip()
    new_pass      = data.get('new_password', '').strip()
    conf_pass     = data.get('confirm_password', '').strip()

    clean_mobile  = ''.join(filter(str.isdigit, mobile_input))

    if not clean_mobile or not otp_input or not new_pass:
        return jsonify({'success': False, 'message': 'Please fill in all required fields.'}), 400

    if new_pass != conf_pass:
        return jsonify({'success': False, 'message': 'Passwords do not match. Please re-enter.'}), 400

    stored_otp    = session.get('reset_otp')
    stored_mobile = session.get('reset_mobile')
    stored_expiry = session.get('reset_expiry')

    if not stored_otp or stored_mobile != clean_mobile:
        return jsonify({'success': False, 'message': 'Invalid or expired OTP session. Please request a new OTP.'}), 400

    if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > stored_expiry:
        return jsonify({'success': False, 'message': 'OTP has expired (valid 5 minutes). Please request a new OTP.'}), 400

    if otp_input != stored_otp:
        return jsonify({'success': False, 'message': 'Incorrect OTP code entered. Please try again.'}), 400

    # OTP is valid! Update password in database
    db.update_user_password_by_mobile(clean_mobile, new_pass)

    # Clear OTP session keys
    session.pop('reset_otp', None)
    session.pop('reset_mobile', None)
    session.pop('reset_expiry', None)

    return jsonify({'success': True, 'message': 'Password reset successfully! You can now sign in with your new password.'})


@app.route('/request-qr-otp', methods=['POST'])
def request_qr_otp():
    data       = request.get_json() or {}
    identifier = data.get('identifier', '').strip()

    if not identifier:
        return jsonify({'success': False, 'message': 'Please enter your registered Username or Mobile Number.'}), 400

    user = db.get_user_by_username(identifier)
    if not user:
        return jsonify({'success': False, 'message': 'No registered account found with this username/mobile.'}), 404

    # Fetch or generate TOTP secret
    secret = user.get('totp_secret')
    if not secret:
        secret = totp_engine.generate_secret()
        db.save_user_totp_secret(user['id'], secret)

    username     = user['username']
    otpauth_uri  = totp_engine.generate_otpauth_uri(username, secret)
    qr_svg       = totp_engine.generate_svg_qr(otpauth_uri)
    current_totp = totp_engine.get_totp_token(secret)

    session['qr_reset_user'] = username

    return jsonify({
        'success': True,
        'username': username,
        'secret': secret,
        'qr_svg': qr_svg,
        'otpauth_uri': otpauth_uri,
        'current_totp': current_totp,
        'message': 'Scan QR Code with Google/Microsoft Authenticator or enter the 6-digit TOTP code.'
    })


@app.route('/verify-qr-otp', methods=['POST'])
def verify_qr_otp():
    data       = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    totp_code  = data.get('totp_code', '').strip()
    new_pass   = data.get('new_password', '').strip()
    conf_pass  = data.get('confirm_password', '').strip()

    if not identifier or not totp_code or not new_pass:
        return jsonify({'success': False, 'message': 'Please fill in all required fields.'}), 400

    if new_pass != conf_pass:
        return jsonify({'success': False, 'message': 'Passwords do not match. Please re-enter.'}), 400

    user = db.get_user_by_username(identifier)
    if not user or not user.get('totp_secret'):
        return jsonify({'success': False, 'message': 'Account or TOTP key not found. Please scan the QR code first.'}), 404

    # Verify TOTP code against secret
    is_valid = totp_engine.verify_totp_token(user['totp_secret'], totp_code)
    if not is_valid:
        return jsonify({'success': False, 'message': 'Invalid TOTP code. Please check your Authenticator app and try again.'}), 400

    # Valid! Update password
    db.update_user_password_by_identifier(identifier, new_pass)
    session.pop('qr_reset_user', None)

    return jsonify({'success': True, 'message': 'Password reset successfully via QR Authenticator! You can now sign in.'})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username      = request.form.get('username', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        password      = request.form.get('password', '').strip()
        user_type     = request.form.get('user_type', 'patient').strip().lower()

        if not username or not password or not mobile_number:
            flash('Please fill in all fields (Username, Mobile Number, and Password).', 'error')
            return render_template('register.html')

        # Mobile number length validation
        clean_mobile = ''.join(filter(str.isdigit, mobile_number))
        if len(clean_mobile) < 10:
            flash('Please enter a valid 10-digit mobile number.', 'error')
            return render_template('register.html')

        role = 'doctor' if user_type in ('doctor', 'admin') else 'patient'
        success, res = db.create_user(username, password, role=role, mobile_number=clean_mobile)
        if success:
            role_label = 'Doctor / Medical Organization' if role == 'doctor' else 'Patient / Individual'
            flash(f"Account '{username}' created successfully as {role_label}! Please sign in.", 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed: {res}', 'error')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Signed out successfully.', 'success')
    return redirect(url_for('login'))


# ─── Application Routes ───────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    recent  = db.get_recent_reports(5, user_id=user_id)
    stats   = db.get_stats(user_id=user_id)
    today_count = db.get_user_today_report_count(user_id)
    return render_template('index.html', recent_reports=recent, stats=stats, today_count=today_count)


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    user_id   = session.get('user_id', 1)
    user_role = session.get('role', 'patient')

    # Upload limit check for Patient accounts (Max 5 reports per day)
    if user_role in ('patient', 'user'):
        today_count = db.get_user_today_report_count(user_id)
        if today_count >= 5:
            flash('Daily Upload Limit Reached: Standard Patient accounts are limited to 5 report uploads per day. Please try again tomorrow or sign in with a Doctor / Medical Organization account.', 'error')
            return redirect(url_for('index'))

    file           = request.files['file']
    raw_name       = request.form.get('patient_name', 'Unknown').strip() or 'Unknown'
    patient_name   = html.escape(raw_name[:100])
    report_type    = request.form.get('report_type', 'lab_report')
    user_id        = session.get('user_id', 1)
    
    try:
        patient_age = max(0, min(120, int(request.form.get('patient_age', 0))))
    except ValueError:
        patient_age = 0
        
    patient_gender = html.escape(request.form.get('patient_gender', 'Unknown')[:20])

    if file.filename == '':
        flash('Please select a file to upload.', 'error')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Unsupported file type.', 'error')
        return redirect(url_for('index'))

    # Security & Isolation: Save file in user-specific local folder
    user_dir    = os.path.join(UPLOAD_FOLDER, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    safe_base   = secure_filename(file.filename) or "report.pdf"
    unique_name = f"{uuid.uuid4().hex}_{safe_base}"
    rel_path    = os.path.join(f"user_{user_id}", unique_name)
    filepath    = os.path.join(user_dir, unique_name)
    file.save(filepath)

    # Diagnostic Pipeline Choice (OCR vs Computer Vision)
    if report_type in ('ecg', 'xray', 'skin'):
        # 🔬 Computer Vision Diagnostic Module
        cv_findings  = cv_analyzer.analyze_image(filepath, report_type=report_type)
        risk_results = cv_findings
        overall_level, overall_score = predictor.overall_risk(risk_results)
    else:
        # 🧪 Lab Report OCR Pipeline
        extracted    = ocr.extract(filepath)
        risk_results = predictor.predict(extracted)
        overall_level, overall_score = predictor.overall_risk(risk_results)

    report_id = db.save_report(
        filename=rel_path,
        patient_name=patient_name,
        patient_age=patient_age,
        patient_gender=patient_gender,
        filepath=filepath,
        user_id=user_id,
        report_type=report_type,
    )
    db.update_report_risk(report_id, overall_score, overall_level)
    db.save_parameters(report_id, risk_results)

    recs = recommender.generate(risk_results)
    db.save_recommendations(report_id, recs)

    alert_sys  = AlertSystem(db)
    new_alerts = alert_sys.generate(report_id, risk_results)
    session['new_sms_alerts'] = new_alerts

    return redirect(url_for('dashboard', report_id=report_id))


@app.route('/dashboard/<int:report_id>')
@login_required
def dashboard(report_id):
    report          = db.get_report(report_id)
    if not report:
        flash('Report not found.', 'error')
        return redirect(url_for('index'))
        
    user_id = session.get('user_id')
    # Data Isolation: Verify report belongs to logged in user or admin
    if session.get('role') != 'admin' and report.get('user_id') != user_id:
        flash('Access denied. You can only view your own health reports.', 'error')
        return redirect(url_for('reports'))

    parameters      = db.get_parameters(report_id)
    recommendations = db.get_recommendations(report_id)
    report_alerts   = db.get_report_alerts(report_id)
    new_sms         = session.pop('new_sms_alerts', [])

    return render_template(
        'dashboard.html',
        report=report,
        parameters=parameters,
        recommendations=recommendations,
        alerts=report_alerts,
        new_sms_alerts=new_sms,
    )


@app.route('/reports')
@login_required
def reports():
    user_id     = session.get('user_id')
    all_reports = db.get_all_reports(user_id=user_id)
    return render_template('reports.html', reports=all_reports)


@app.route('/alerts')
@login_required
def alerts_page():
    user_id     = session.get('user_id') if session.get('role') not in ('doctor', 'admin') else None
    all_alerts  = db.get_all_alerts(user_id=user_id)
    unread      = db.get_unread_alert_count(user_id=user_id)
    db.mark_all_alerts_read(user_id=user_id)
    return render_template('alerts.html', alerts=all_alerts, unread_count=unread)


@app.route('/delete-report/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    report = db.get_report(report_id)
    user_id = session.get('user_id')
    if report:
        if session.get('role') == 'admin' or report.get('user_id') == user_id:
            fp = os.path.join(UPLOAD_FOLDER, report['filename'])
            if os.path.exists(fp):
                os.remove(fp)
            db.delete_report(report_id)
            flash('Report deleted successfully.', 'success')
        else:
            flash('Access denied.', 'error')
    return redirect(url_for('reports'))


# ─── FHIR Export & Multi-Lingual Translation Endpoints ─────────────────────────

@app.route('/export-fhir/<int:report_id>')
@login_required
def export_fhir(report_id):
    report = db.get_report(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
        
    parameters  = db.get_parameters(report_id)
    fhir_bundle = fhir_engine.export_bundle(report, parameters)
    
    response_data = json.dumps(fhir_bundle, indent=2)
    return Response(
        response_data,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename=FHIR_Report_{report_id}.json'}
    )


@app.route('/api/translate', methods=['POST'])
@login_required
def api_translate():
    data      = request.get_json() or {}
    text      = data.get('text', '')
    lang      = data.get('lang', 'en')
    report_id = data.get('report_id')

    if report_id:
        report     = db.get_report(report_id)
        parameters = db.get_parameters(report_id) if report else []
        if report:
            summary = translator.get_translated_summary(report, parameters, lang=lang)
            return jsonify({'original': text, 'translated': summary, 'summary': summary, 'lang': lang})

    translated = translator.translate_text(text, lang=lang)
    return jsonify({'original': text, 'translated': translated, 'summary': translated, 'lang': lang})


# ─── API endpoints ─────────────────────────────────────────────────────────────

@app.route('/api/report-data/<int:report_id>')
@login_required
def api_report_data(report_id):
    params = db.get_parameters(report_id)
    report = db.get_report(report_id)
    return jsonify({'parameters': params, 'report': report})


@app.route('/api/dismiss-alert/<int:alert_id>', methods=['POST'])
@login_required
def api_dismiss_alert(alert_id):
    db.dismiss_alert(alert_id)
    return jsonify({'success': True})


@app.route('/api/unread-alerts')
@login_required
def api_unread_alerts():
    user_id = session.get('user_id') if session.get('role') not in ('doctor', 'admin') else None
    return jsonify({'count': db.get_unread_alert_count(user_id=user_id)})


@app.route('/api/health-trends')
@login_required
def api_health_trends():
    user_id = session.get('user_id')
    return jsonify(db.get_health_trends(user_id=user_id))


@app.route('/api/stats')
@login_required
def api_stats():
    user_id = session.get('user_id')
    return jsonify(db.get_stats(user_id=user_id))


@app.route('/download-sample/<path:filename>')
def download_sample(filename):
    safe_name = secure_filename(os.path.basename(filename))
    sample_dir = os.path.join(app.root_path, 'static', 'sample_reports')
    return send_from_directory(sample_dir, safe_name, as_attachment=True)


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    db.init_db()
    print("=" * 55)
    print("  MediLensAI - Offline Health Intelligence System")
    print("  Running locally at http://127.0.0.1:5000")
    print("  Mobile LAN access: http://<your-pc-ip>:5000")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)
