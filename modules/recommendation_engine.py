class RecommendationEngine:
    """
    Generates personalized health recommendations based on risk levels
    for each detected medical parameter. Fully rule-based, offline.
    """

    _RECS = {
        'blood_sugar': {
            'Low': [
                ('Diet',      'Eat small, frequent meals every 2–3 hours to stabilise blood sugar.'),
                ('Lifestyle', 'Never skip breakfast — it helps maintain morning glucose levels.'),
                ('Monitor',   'Check blood sugar regularly to catch hypoglycaemic episodes early.'),
            ],
            'Normal': [
                ('Lifestyle', 'Great! Keep up your balanced diet and active lifestyle.'),
                ('Diet',      'Prioritise fibre-rich foods (oats, legumes, vegetables) to sustain normal levels.'),
            ],
            'Moderate': [
                ('Diet',      'Cut refined sugars, white rice, and sugary beverages from your diet.'),
                ('Exercise',  'Walk or exercise for at least 30 minutes daily to improve insulin sensitivity.'),
                ('Monitor',   'Re-test fasting blood sugar in 4–6 weeks.'),
                ('Medical',   'Speak with your doctor — pre-diabetes is reversible with lifestyle changes.'),
            ],
            'High': [
                ('Medical',   'Blood sugar is in the diabetic range. Consult your doctor without delay.'),
                ('Diet',      'Follow a strict low-glycaemic diet. Eliminate sweets and processed carbs.'),
                ('Exercise',  'Daily physical activity significantly improves blood sugar control.'),
                ('Monitor',   'Monitor fasting and post-meal blood sugar at least twice daily.'),
            ],
            'Critical': [
                ('Medical',   'URGENT — Blood sugar is critically elevated. Seek medical care immediately.'),
                ('Diet',      'Avoid ALL sugary and high-carbohydrate foods until medically reviewed.'),
            ],
        },
        'hemoglobin': {
            'Low': [
                ('Medical',   'Anaemia detected (Low Hemoglobin). Consult your doctor for an iron & CBC evaluation.'),
                ('Diet',      'Eat iron-rich foods daily: spinach, beetroot, pomegranate, legumes, lean meats.'),
                ('Supplement','Pair iron-rich foods with Vitamin C (citrus, lemons) to maximize iron absorption.'),
                ('Lifestyle', 'Ensure adequate rest and monitor for symptoms like fatigue, dizziness, or paleness.'),
            ],
            'Critical Low': [
                ('Medical',   'URGENT — Severe anaemia detected. Seek immediate medical attention.'),
                ('Diet',      'High-iron nutrition required under medical supervision.'),
                ('Monitor',   'Urgent full blood count (CBC) and serum ferritin testing needed.'),
            ],
            'Critical': [
                ('Medical',   'URGENT — Hemoglobin is dangerously low. Go to a hospital immediately.'),
                ('Diet',      'Increase iron intake: spinach, red meat, lentils, fortified cereals.'),
            ],
            'High': [
                ('Medical',   'Anaemia detected. Consult your doctor for a full blood workup.'),
                ('Diet',      'Eat iron-rich foods daily: leafy greens, legumes, lean meats.'),
                ('Supplement','Iron supplements may be prescribed — do not self-medicate.'),
            ],
            'Moderate': [
                ('Diet',      'Pair iron-rich foods with vitamin C (citrus, tomatoes) to boost absorption.'),
                ('Monitor',   'Re-check hemoglobin in 6 weeks.'),
            ],
            'Normal': [
                ('Lifestyle', 'Hemoglobin is in the healthy range. Maintain your current diet.'),
            ],
        },
        'cholesterol': {
            'Normal': [
                ('Diet',      'Continue your heart-healthy diet low in saturated fat.'),
            ],
            'Moderate': [
                ('Diet',      'Reduce saturated fat and trans fat. Increase soluble fibre (oats, barley).'),
                ('Exercise',  'Aim for 150 minutes of aerobic exercise per week to raise HDL cholesterol.'),
                ('Lifestyle', 'Quit smoking if applicable — it lowers HDL and raises LDL.'),
            ],
            'High': [
                ('Medical',   'High cholesterol — consult a doctor about statin therapy.'),
                ('Diet',      'Follow a strict heart-healthy diet. Eliminate fried and processed foods.'),
                ('Exercise',  'Regular cardio exercise is essential for improving cholesterol profile.'),
            ],
        },
        'systolic_bp': {
            'Low': [
                ('Hydration', 'Drink adequate water and consider moderate salt intake.'),
                ('Lifestyle', 'Avoid prolonged standing; rise slowly to prevent dizziness.'),
            ],
            'Normal': [
                ('Lifestyle', 'Excellent! Maintain your healthy blood pressure with regular exercise.'),
            ],
            'Moderate': [
                ('Diet',      'Reduce sodium to under 2,300 mg/day. Follow the DASH diet.'),
                ('Exercise',  'Regular aerobic exercise (walking, cycling) lowers blood pressure.'),
                ('Lifestyle', 'Practise stress-reduction techniques: deep breathing, yoga, meditation.'),
            ],
            'High': [
                ('Medical',   'High blood pressure detected. Seek medical evaluation for treatment.'),
                ('Diet',      'DASH diet: high potassium (bananas, sweet potatoes), very low sodium.'),
                ('Monitor',   'Measure blood pressure daily and log the readings.'),
            ],
            'Critical': [
                ('Medical',   'URGENT — Hypertensive crisis. Call emergency services immediately.'),
            ],
        },
        'diastolic_bp': {
            'Low': [
                ('Hydration', 'Increase fluid intake and avoid prolonged heat exposure.'),
            ],
            'Normal': [
                ('Lifestyle', 'Diastolic BP is normal. Keep up your healthy habits.'),
            ],
            'Moderate': [
                ('Diet',      'Limit caffeine and alcohol; both elevate diastolic pressure.'),
                ('Exercise',  'Gentle aerobic activity helps improve diastolic function.'),
            ],
            'High': [
                ('Medical',   'Elevated diastolic BP. Consult a physician for appropriate treatment.'),
            ],
            'Critical': [
                ('Medical',   'URGENT — Extremely high diastolic pressure. Seek emergency care now.'),
            ],
        },
        'wbc': {
            'Normal': [
                ('Lifestyle', 'WBC is normal. Support your immune health with a balanced diet.'),
            ],
            'Moderate': [
                ('Medical',   'Abnormal WBC may indicate infection or immune irregularity. See a doctor.'),
                ('Lifestyle', 'If WBC is low, avoid crowds and practise strict hygiene to prevent infection.'),
            ],
            'High': [
                ('Medical',   'Significantly abnormal WBC. Urgent medical evaluation is required.'),
            ],
        },
        'rbc': {
            'Normal': [
                ('Diet',      'RBC is healthy. Maintain adequate iron and B12 intake.'),
            ],
            'Moderate': [
                ('Diet',      'Include vitamin B12 and folate-rich foods: eggs, fish, leafy greens.'),
                ('Monitor',   'Re-test RBC in 6–8 weeks.'),
            ],
            'High': [
                ('Medical',   'Low RBC count suggests anaemia or nutritional deficiency. See a doctor.'),
            ],
        },
        'creatinine': {
            'Low': [
                ('Hydration', 'Stay well-hydrated to support kidney filtration.'),
            ],
            'Normal': [
                ('Hydration', 'Creatinine is normal. Drink 8 glasses of water daily.'),
            ],
            'Moderate': [
                ('Medical',   'Slightly elevated creatinine — monitor kidney function closely.'),
                ('Hydration', 'Drink at least 2–3 litres of water daily.'),
                ('Diet',      'Reduce red meat and high-protein foods to ease kidney workload.'),
            ],
            'High': [
                ('Medical',   'Elevated creatinine suggests reduced kidney function. See a nephrologist.'),
                ('Diet',      'Avoid high-protein foods, excessive salt, and NSAIDs.'),
            ],
            'Critical': [
                ('Medical',   'URGENT — Creatinine is severely elevated. Possible kidney failure. Seek immediate care.'),
            ],
        },
        'urea': {
            'Normal': [
                ('Hydration', 'Blood urea is normal. Maintain good hydration.'),
            ],
            'Moderate': [
                ('Diet',      'Reduce protein intake moderately and drink more water.'),
                ('Monitor',   'Re-check urea in 4 weeks.'),
            ],
            'High': [
                ('Medical',   'High blood urea may indicate impaired kidney function. Consult a doctor.'),
                ('Diet',      'Reduce dietary protein and avoid dehydration.'),
            ],
        },
        'uric_acid': {
            'Normal': [
                ('Diet',      'Uric acid is normal. Limit high-purine foods as a preventive measure.'),
            ],
            'High': [
                ('Medical',   'High uric acid can cause gout and kidney stones. See a doctor.'),
                ('Diet',      'Avoid red meat, organ meats, shellfish, beer, and sugary drinks.'),
                ('Hydration', 'Drink plenty of water to help flush uric acid from the body.'),
            ],
        },
    }

    def generate(self, risk_results: list) -> list:
        recommendations = []
        for param in risk_results:
            if param['value'] is None:
                continue
            param_recs = self._RECS.get(param['name'], {})
            level_recs = param_recs.get(param['risk_level'], [])
            for category, text in level_recs:
                recommendations.append({
                    'parameter':    param['name'],
                    'display_name': param['display_name'],
                    'category':     category,
                    'text':         text,
                    'risk_level':   param['risk_level'],
                })
        return recommendations
