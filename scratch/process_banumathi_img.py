import sys
import os
from PIL import Image

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

# Render BANUMATHI image from artifact directory or user uploaded image
banumathi_img_path = r'C:\Users\nandh\.gemini\antigravity\brain\d6b6313e-06cc-4817-a418-39c17999a602\.user_uploaded\media__1785666173111.png'

if os.path.exists(banumathi_img_path):
    print("Found BANUMATHI image! Running OCR...")
    extracted = ocr.extract_from_image(banumathi_img_path)
    values = ocr.parse_values(extracted)
    print(f"Extracted values: {values}")
    
    risk_results = predictor.predict(values)
    overall_level, overall_score = predictor.overall_risk(risk_results)
    
    print(f"Overall Risk: {overall_level} ({overall_score})")
    
    # Save to report #5 in DB
    report_id = 5
    db.update_report_risk(report_id, overall_score, overall_level)
    db.save_parameters(report_id, risk_results)
    
    recs = recommender.generate(risk_results)
    db.save_recommendations(report_id, recs)
    
    new_alerts = alert_sys.generate(report_id, risk_results)
    print(f"Fired {len(new_alerts)} health alerts for BANUMATHI!")
    print("SUCCESS! Report #5 updated with complete BANUMATHI CBC data.")
else:
    print(f"File not found: {banumathi_img_path}")
