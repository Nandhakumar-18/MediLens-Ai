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

banumathi_pdf = r'C:\Users\nandh\.gemini\antigravity\brain\d6b6313e-06cc-4817-a418-39c17999a602\.user_uploaded\media__1785681705193.pdf'

print(f"Testing OCR on BANUMATHI PDF: {banumathi_pdf}")
values = ocr.extract(banumathi_pdf)
print(f"\nExtracted parameters dictionary:\n{values}")

risk_results = predictor.predict(values)
overall_level, overall_score = predictor.overall_risk(risk_results)

print(f"\nOverall Risk: {overall_level} ({overall_score})")

# Save to report #5 in DB
report_id = 5
db.update_report_risk(report_id, overall_score, overall_level)
db.save_parameters(report_id, risk_results)

recs = recommender.generate(risk_results)
db.save_recommendations(report_id, recs)

new_alerts = alert_sys.generate(report_id, risk_results)
print(f"\nFired {len(new_alerts)} health alerts for BANUMATHI:")
for a in new_alerts:
    print(" -", a['message'])

print("\nSUCCESS! Report #5 in database updated with full BANUMATHI CBC data.")
