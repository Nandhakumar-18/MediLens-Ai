class RiskPredictor:
    """
    Rule-based health risk predictor.
    Analyses extracted OCR values against clinical reference ranges and
    returns a risk level (Normal / Low / Moderate / High / Critical)
    and a numeric risk score (0–4) for each parameter.
    """

    PARAMETERS = {
        'blood_sugar': {
            'display_name': 'Blood Sugar (Fasting)',
            'unit': 'mg/dL',
            'normal_min': 70,
            'normal_max': 100,
            'icon': '🩸',
            'ranges': [
                (0,    70,           'Low',      2),
                (70,   100,          'Normal',   0),
                (100,  126,          'Moderate', 2),
                (126,  200,          'High',     3),
                (200,  float('inf'), 'Critical', 4),
            ],
        },
        'hemoglobin': {
            'display_name': 'Hemoglobin',
            'unit': 'g/dL',
            'normal_min': 12.0,
            'normal_max': 17.5,
            'icon': '💉',
            'ranges': [
                (0,    8.0,          'Critical Low', 4),
                (8.0,  10.0,         'Low',          3),
                (10.0, 12.0,         'Low',          2),
                (12.0, 17.5,         'Normal',       0),
                (17.5, float('inf'), 'High',         2),
            ],
        },
        'cholesterol': {
            'display_name': 'Total Cholesterol',
            'unit': 'mg/dL',
            'normal_min': 0,
            'normal_max': 200,
            'icon': '🫀',
            'ranges': [
                (0,   200,          'Normal',   0),
                (200, 240,          'Moderate', 2),
                (240, float('inf'), 'High',     3),
            ],
        },
        'systolic_bp': {
            'display_name': 'Systolic Blood Pressure',
            'unit': 'mmHg',
            'normal_min': 90,
            'normal_max': 120,
            'icon': '💓',
            'ranges': [
                (0,   90,           'Low',      1),
                (90,  120,          'Normal',   0),
                (120, 130,          'Moderate', 1),
                (130, 140,          'Moderate', 2),
                (140, 180,          'High',     3),
                (180, float('inf'), 'Critical', 4),
            ],
        },
        'diastolic_bp': {
            'display_name': 'Diastolic Blood Pressure',
            'unit': 'mmHg',
            'normal_min': 60,
            'normal_max': 80,
            'icon': '💗',
            'ranges': [
                (0,   60,           'Low',      1),
                (60,  80,           'Normal',   0),
                (80,  90,           'Moderate', 2),
                (90,  120,          'High',     3),
                (120, float('inf'), 'Critical', 4),
            ],
        },
        'wbc': {
            'display_name': 'WBC Count',
            'unit': 'cells/μL',
            'normal_min': 4500,
            'normal_max': 11000,
            'icon': '🦠',
            'ranges': [
                (0,     4500,          'Low',      2),
                (4500,  11000,         'Normal',   0),
                (11000, 15000,         'Moderate', 2),
                (15000, float('inf'),  'High',     3),
            ],
        },
        'rbc': {
            'display_name': 'RBC Count',
            'unit': 'million/μL',
            'normal_min': 4.0,
            'normal_max': 5.5,
            'icon': '🔴',
            'ranges': [
                (0,   3.5,          'Low',      3),
                (3.5, 4.0,          'Low',      2),
                (4.0, 5.5,          'Normal',   0),
                (5.5, float('inf'), 'High',     2),
            ],
        },
        'mcv': {
            'display_name': 'Mean Cell Volume (MCV)',
            'unit': 'fL',
            'normal_min': 76.0,
            'normal_max': 93.0,
            'icon': '🩸',
            'ranges': [
                (0,    76.0,         'Low',      2),
                (76.0, 93.0,         'Normal',   0),
                (93.0, float('inf'), 'High',     2),
            ],
        },
        'mch': {
            'display_name': 'Mean Cell Hemoglobin (MCH)',
            'unit': 'pg',
            'normal_min': 27.0,
            'normal_max': 32.0,
            'icon': '💉',
            'ranges': [
                (0,    27.0,         'Low',      2),
                (27.0, 32.0,         'Normal',   0),
                (32.0, float('inf'), 'High',     2),
            ],
        },
        'mchc': {
            'display_name': 'Mean Cell Hb Conc (MCHC)',
            'unit': 'g/dL',
            'normal_min': 32.0,
            'normal_max': 36.0,
            'icon': '🩸',
            'ranges': [
                (0,    32.0,         'Low',      2),
                (32.0, 36.0,         'Normal',   0),
                (36.0, float('inf'), 'High',     2),
            ],
        },
        'hematocrit': {
            'display_name': 'Hematocrit (PCV)',
            'unit': '%',
            'normal_min': 37.0,
            'normal_max': 47.0,
            'icon': '📊',
            'ranges': [
                (0,    37.0,         'Low',      2),
                (37.0, 47.0,         'Normal',   0),
                (47.0, float('inf'), 'High',     2),
            ],
        },
        'platelets': {
            'display_name': 'Platelet Count',
            'unit': 'Thousand/μL',
            'normal_min': 150.0,
            'normal_max': 450.0,
            'icon': '🩸',
            'ranges': [
                (0,     150.0,        'Low',      3),
                (150.0, 450.0,        'Normal',   0),
                (450.0, float('inf'), 'High',     2),
            ],
        },
        'lymphocytes': {
            'display_name': 'Lymphocytes',
            'unit': '%',
            'normal_min': 20.0,
            'normal_max': 40.0,
            'icon': '🛡️',
            'ranges': [
                (0,    20.0,         'Low',      2),
                (20.0, 40.0,         'Normal',   0),
                (40.0, float('inf'), 'High',     2),
            ],
        },
        'rdw_sd': {
            'display_name': 'RDW-SD',
            'unit': 'fL',
            'normal_min': 35.0,
            'normal_max': 56.0,
            'icon': '📈',
            'ranges': [
                (0,    35.0,         'Low',      1),
                (35.0, 56.0,         'Normal',   0),
                (56.0, float('inf'), 'High',     2),
            ],
        },
        'rdw_cv': {
            'display_name': 'RDW-CV',
            'unit': '%',
            'normal_min': 11.0,
            'normal_max': 16.0,
            'icon': '📈',
            'ranges': [
                (0,    11.0,         'Low',      1),
                (11.0, 16.0,         'Normal',   0),
                (16.0, float('inf'), 'High',     2),
            ],
        },
        'creatinine': {
            'display_name': 'Creatinine',
            'unit': 'mg/dL',
            'normal_min': 0.6,
            'normal_max': 1.3,
            'icon': '🫘',
            'ranges': [
                (0,   0.6,          'Low',      1),
                (0.6, 1.3,          'Normal',   0),
                (1.3, 1.8,          'Moderate', 2),
                (1.8, 3.0,          'High',     3),
                (3.0, float('inf'), 'Critical', 4),
            ],
        },
        'urea': {
            'display_name': 'Blood Urea',
            'unit': 'mg/dL',
            'normal_min': 15,
            'normal_max': 45,
            'icon': '🧪',
            'ranges': [
                (0,  15,           'Low',      1),
                (15, 45,           'Normal',   0),
                (45, 60,           'Moderate', 2),
                (60, float('inf'), 'High',     3),
            ],
        },
        'uric_acid': {
            'display_name': 'Uric Acid',
            'unit': 'mg/dL',
            'normal_min': 2.4,
            'normal_max': 7.0,
            'icon': '⚗️',
            'ranges': [
                (0,   2.4,          'Low',      1),
                (2.4, 7.0,          'Normal',   0),
                (7.0, float('inf'), 'High',     3),
            ],
        },
    }

    def get_gender_info(self, name: str, gender: str) -> dict:
        info = dict(self.PARAMETERS[name])
        g = str(gender).strip().lower()
        if g in ('male', 'm'):
            if name == 'hemoglobin':
                info['normal_min'], info['normal_max'] = 13.5, 17.5
                info['ranges'] = [(0, 8.0, 'Critical Low', 4), (8.0, 11.0, 'Low', 3), (11.0, 13.5, 'Low', 2), (13.5, 17.5, 'Normal', 0), (17.5, float('inf'), 'High', 2)]
            elif name == 'rbc':
                info['normal_min'], info['normal_max'] = 4.5, 5.9
                info['ranges'] = [(0, 3.8, 'Low', 3), (3.8, 4.5, 'Low', 2), (4.5, 5.9, 'Normal', 0), (5.9, float('inf'), 'High', 2)]
            elif name == 'hematocrit':
                info['normal_min'], info['normal_max'] = 41.0, 50.0
                info['ranges'] = [(0, 41.0, 'Low', 2), (41.0, 50.0, 'Normal', 0), (50.0, float('inf'), 'High', 2)]
            elif name == 'creatinine':
                info['normal_min'], info['normal_max'] = 0.7, 1.3
                info['ranges'] = [(0, 0.7, 'Low', 1), (0.7, 1.3, 'Normal', 0), (1.3, 1.8, 'Moderate', 2), (1.8, 3.0, 'High', 3), (3.0, float('inf'), 'Critical', 4)]
            elif name == 'uric_acid':
                info['normal_min'], info['normal_max'] = 3.4, 7.0
                info['ranges'] = [(0, 3.4, 'Low', 1), (3.4, 7.0, 'Normal', 0), (7.0, float('inf'), 'High', 3)]
        elif g in ('female', 'f'):
            if name == 'hemoglobin':
                info['normal_min'], info['normal_max'] = 12.0, 15.5
                info['ranges'] = [(0, 8.0, 'Critical Low', 4), (8.0, 10.0, 'Low', 3), (10.0, 12.0, 'Low', 2), (12.0, 15.5, 'Normal', 0), (15.5, float('inf'), 'High', 2)]
            elif name == 'rbc':
                info['normal_min'], info['normal_max'] = 4.1, 5.1
                info['ranges'] = [(0, 3.5, 'Low', 3), (3.5, 4.1, 'Low', 2), (4.1, 5.1, 'Normal', 0), (5.1, float('inf'), 'High', 2)]
            elif name == 'hematocrit':
                info['normal_min'], info['normal_max'] = 36.0, 46.0
                info['ranges'] = [(0, 36.0, 'Low', 2), (36.0, 46.0, 'Normal', 0), (46.0, float('inf'), 'High', 2)]
            elif name == 'creatinine':
                info['normal_min'], info['normal_max'] = 0.55, 1.02
                info['ranges'] = [(0, 0.55, 'Low', 1), (0.55, 1.02, 'Normal', 0), (1.02, 1.5, 'Moderate', 2), (1.5, 2.5, 'High', 3), (2.5, float('inf'), 'Critical', 4)]
            elif name == 'uric_acid':
                info['normal_min'], info['normal_max'] = 2.4, 6.0
                info['ranges'] = [(0, 2.4, 'Low', 1), (2.4, 6.0, 'Normal', 0), (6.0, float('inf'), 'High', 3)]
        return info

    def _classify_custom(self, ranges: list, value: float):
        for lo, hi, level, score in ranges:
            if lo <= value < hi:
                return level, score
        return 'Unknown', 0

    def predict(self, extracted: dict, gender: str = 'Unknown') -> list:
        results = []
        for name in self.PARAMETERS.keys():
            info  = self.get_gender_info(name, gender)
            value = extracted.get(name)
            entry = {
                'name': name,
                'display_name': info['display_name'],
                'unit': info['unit'],
                'normal_min': info['normal_min'],
                'normal_max': info['normal_max'],
                'icon': info['icon'],
                'value': value,
                'risk_level': 'Not Detected',
                'risk_score': 0,
            }
            if value is not None:
                level, score = self._classify_custom(info['ranges'], value)
                entry['risk_level'] = level
                entry['risk_score'] = score
            results.append(entry)
        return results

    def overall_risk(self, results: list) -> tuple:
        detected = [r for r in results if r['value'] is not None]
        if not detected:
            return 'Unknown', 0.0
        scores = [r['risk_score'] for r in detected]
        avg = sum(scores) / len(scores)
        mx  = max(scores)
        if mx >= 4 or avg >= 3:
            return 'Critical', round(avg, 2)
        if mx >= 3 or avg >= 2:
            return 'High', round(avg, 2)
        if avg >= 1:
            return 'Moderate', round(avg, 2)
        return 'Normal', round(avg, 2)
