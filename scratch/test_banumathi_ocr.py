import sys
import os
from PIL import Image

sys.path.append(r'c:\Users\nandh\OneDrive\Documents\Project\MediLensAI')

from modules.ocr_extractor import OCRExtractor

extractor = OCRExtractor()

# Test pattern matching on raw text from Banumathi report
raw_sample_text = """
Department of Camp
Hematology
Patient Name: Banumathi
Complete Blood Count CBC (Hematology)
White Blood Cell Count 9.2 4 - 11 /cumm
R B C Count 5.40 4 - 5.50 Million/MicroL
Haemoglobin 12.9 11 - 15 gm/dL
Hematocrit 40.6 37 - 47 %
Neutrophils NA 40 - 70 %
Lymphocytes 38.6 20 - 40 %
Mixed NA 2 - 8 %
Mean Cell Volume 75.2 76 - 93 fL
Mean Cell Hemoglobin 23.9 27 - 32 pg
Mean Cell Hb Concentration 31.8 32 - 36 g/dL
Rdw Sd 45.9 35 - 56 fL
Rdw Cv 16.0 11 - 16 %
Platelet Count 280 150 - 450 Thousand/MicroL
"""

extracted = extractor.parse_text(raw_sample_text)
print("Extracted dictionary:")
print(extracted)
