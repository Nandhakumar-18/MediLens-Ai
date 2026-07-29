class AlertSystem:
    """
    Generates health alerts for abnormal parameter values and simulates
    SMS notifications stored locally in SQLite. Fully offline.
    """

    # Only fire alerts for these risk levels (Normal is silent)
    _TEMPLATES = {
        'blood_sugar': {
            'Low':      '[WARNING] Blood sugar is LOW ({value} mg/dL) - risk of hypoglycaemia.',
            'Moderate': '[WARNING] Blood sugar is BORDERLINE HIGH ({value} mg/dL) - pre-diabetic range.',
            'High':     '[ALERT] Blood sugar is HIGH ({value} mg/dL) - diabetic range. Seek medical advice.',
            'Critical': '[CRITICAL] Blood sugar is dangerously high ({value} mg/dL). Emergency care needed!',
        },
        'hemoglobin': {
            'Low':          '[ALERT] Hemoglobin is LOW ({value} g/dL) - anaemia detected. See a doctor.',
            'Critical Low': '[CRITICAL] Hemoglobin is dangerously low ({value} g/dL). Urgent medical attention required!',
            'Moderate':     '[WARNING] Hemoglobin is BELOW NORMAL ({value} g/dL) - mild anaemia possible.',
            'High':         '[ALERT] Hemoglobin is LOW ({value} g/dL) - anaemia detected. See a doctor.',
            'Critical':     '[CRITICAL] Hemoglobin is severely low ({value} g/dL). Urgent medical attention!',
        },
        'cholesterol': {
            'Moderate': '[WARNING] Cholesterol is BORDERLINE HIGH ({value} mg/dL) - diet changes recommended.',
            'High':     '[ALERT] Cholesterol is HIGH ({value} mg/dL) - cardiovascular risk elevated.',
        },
        'systolic_bp': {
            'Low':      '[WARNING] Systolic BP is LOW ({value} mmHg) - monitor for dizziness or fainting.',
            'Moderate': '[WARNING] Systolic BP is ELEVATED ({value} mmHg) - monitor closely.',
            'High':     '[ALERT] Systolic BP is HIGH ({value} mmHg) - hypertension. Medical consultation required.',
            'Critical': '[CRITICAL] Hypertensive crisis ({value} mmHg). Call emergency services immediately!',
        },
        'diastolic_bp': {
            'Low':      '[WARNING] Diastolic BP is LOW ({value} mmHg) - possible hypotension.',
            'Moderate': '[WARNING] Diastolic BP is ELEVATED ({value} mmHg).',
            'High':     '[ALERT] Diastolic BP is HIGH ({value} mmHg). Medical evaluation required.',
            'Critical': '[CRITICAL] Extremely high diastolic BP ({value} mmHg). Seek emergency care!',
        },
        'creatinine': {
            'Moderate': '[WARNING] Creatinine is SLIGHTLY ELEVATED ({value} mg/dL) - monitor kidney function.',
            'High':     '[ALERT] Creatinine is HIGH ({value} mg/dL) - possible kidney dysfunction.',
            'Critical': '[CRITICAL] Creatinine is severely elevated ({value} mg/dL). Possible kidney failure!',
        },
        'wbc': {
            'Moderate': '[WARNING] WBC count is ABNORMAL ({value} cells/uL) - possible infection or immune issue.',
            'High':     '[ALERT] WBC count is SIGNIFICANTLY ABNORMAL ({value} cells/uL). Immediate evaluation needed.',
        },
        'rbc': {
            'Moderate': '[WARNING] RBC count is SLIGHTLY LOW ({value} million/uL) - monitor for anaemia.',
            'High':     '[ALERT] RBC count is LOW ({value} million/uL) - anaemia likely.',
        },
        'urea': {
            'Moderate': '[WARNING] Blood urea is SLIGHTLY ELEVATED ({value} mg/dL).',
            'High':     '[ALERT] Blood urea is HIGH ({value} mg/dL) - possible kidney impairment.',
        },
        'uric_acid': {
            'High': '[WARNING] Uric acid is HIGH ({value} mg/dL) - risk of gout or kidney stones.',
        },
    }

    def __init__(self, db):
        self.db = db

    def generate(self, report_id: int, risk_results: list) -> list:
        fired = []
        for param in risk_results:
            if param['value'] is None:
                continue
            tmpl = self._TEMPLATES.get(param['name'], {}).get(param['risk_level'])
            if tmpl:
                message = tmpl.format(value=round(param['value'], 2))
                self.db.save_alert(
                    report_id=report_id,
                    parameter_name=param['name'],
                    message=message,
                    severity=param['risk_level'],
                )
                fired.append({
                    'parameter': param['name'],
                    'message':   message,
                    'severity':  param['risk_level'],
                })
        
        if fired:
            # Console simulation log
            print("\n" + "="*60)
            print("[SMS SIMULATOR] SENDING HEALTH ALERTS")
            print("="*60)
            for alert in fired:
                print(f"TO: Patient Contact (Simulated)")
                print(f"MSG: {alert['message']}")
                print("-" * 60)
            print("="*60 + "\n")

            # Local file simulation log
            try:
                import os
                from datetime import datetime
                log_path = os.path.join(os.path.dirname(__file__), '..', 'sms_simulation_log.txt')
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n--- SMS Batch - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                    for alert in fired:
                        f.write(f"TO: Patient Contact\nMSG: {alert['message']}\n\n")
            except Exception as e:
                print(f"[AlertSystem] Failed to write to SMS log file: {e}")

        return fired
