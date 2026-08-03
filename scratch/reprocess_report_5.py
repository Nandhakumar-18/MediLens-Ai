import sys
import os

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

reports = db.get_recent_reports(10)
print(f"Found {len(reports)} reports in DB:")

for r in reports:
    report_id = r['id']
    filename = r['filename']
    filepath = os.path.join(r'c:\Users\nandh\OneDrive\Documents\Project\MediLensAI\static\uploads', filename)
    print(f"ID: {report_id} | Patient: {r['patient_name']} | File: {filepath}")
    
    if os.path.exists(filepath):
        extracted = ocr.extract(filepath)
        print(f"--> Extracted values for {r['patient_name']}: {extracted}")
        
        risk_results = predictor.predict(extracted)
        overall_level, overall_score = predictor.overall_risk(risk_results)
        
        print(f"--> Overall Risk: {overall_level} ({overall_score})")
        
        db.update_report_risk(report_id, overall_score, overall_level)
        db.save_parameters(report_id, risk_results)
        
        recs = recommender.generate(risk_results)
        db.save_recommendations(report_id, recs)
        
        new_alerts = alert_sys.generate(report_id, risk_results)
        print(f"--> Fired {len(new_alerts)} alerts!")
    else:
        print(f"ERROR: File not found at {filepath}")
