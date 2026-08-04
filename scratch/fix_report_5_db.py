import sys
import os
import shutil

sys.path.append(r'c:\Users\nandh\OneDrive\Documents\Project\MediLensAI')

from database.db import Database
from modules.ocr_extractor import OCRExtractor
from modules.risk_predictor import RiskPredictor
from modules.recommendation_engine import RecommendationEngine
from modules.alert_system import AlertSystem

db = Database()
ocr = OCRExtractor()
predictor = RiskPredictor()
recommender = RecommendationEngine()
alert_sys = AlertSystem(db)

# 1. Source real BANUMATHI PDF file
src_pdf = r'C:\Users\nandh\.gemini\antigravity\brain\d6b6313e-06cc-4817-a418-39c17999a602\.user_uploaded\media__1785681705193.pdf'

# 2. Get report 5 from DB
report_5 = db.get_report(5)
if report_5:
    dest_path = os.path.join(r'c:\Users\nandh\OneDrive\Documents\Project\MediLensAI\static\uploads', report_5['filename'])
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(src_pdf, dest_path)
    print(f"Copied real BANUMATHI PDF to: {dest_path}")

    # 3. Extract OCR parameters
    extracted = ocr.extract(dest_path)
    print(f"Extracted OCR values: {extracted}")

    risk_results = predictor.predict(extracted)
    overall_level, overall_score = predictor.overall_risk(risk_results)

    # 4. Clear existing parameters for report 5
    conn = db.get_connection()
    conn.execute('DELETE FROM health_parameters WHERE report_id=5')
    conn.execute('DELETE FROM recommendations WHERE report_id=5')
    conn.execute('DELETE FROM alerts WHERE report_id=5')
    conn.commit()
    conn.close()

    # 5. Save new CBC parameters, risk score, recommendations, and alerts
    db.update_report_risk(5, overall_score, overall_level)
    db.save_parameters(5, risk_results)

    recs = recommender.generate(risk_results)
    db.save_recommendations(5, recs)

    new_alerts = alert_sys.generate(5, risk_results)

    print(f"--> Saved {len([r for r in risk_results if r['value'] is not None])} parameters to Report #5")
    print(f"--> Overall Risk: {overall_level} ({overall_score})")
    print(f"--> Fired {len(new_alerts)} health alerts")
    print("SUCCESS! Report #5 in database is now 100% updated!")
else:
    print("Report 5 not found in DB")
