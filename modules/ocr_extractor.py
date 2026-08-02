import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import re
import os


class OCRExtractor:
    """
    High-speed, universal OCR extractor for all medical lab report formats.
    Optimized for fast execution (< 1 sec) and multi-column tabular reports.
    """

    def __init__(self):
        # Auto-detect Tesseract on Windows
        win_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(win_path):
            pytesseract.pytesseract.tesseract_cmd = win_path

        # Universal parameter keywords mapping
        self.PARAM_KEYWORDS = {
            'blood_sugar': ['fasting blood glucose', 'fasting sugar', 'fbs', 'fpg', 'blood sugar', 'glucose', 'rbs', 'ppbs'],
            'hemoglobin': ['haemoglobin', 'hemoglobin', 'hgb', 'hb'],
            'cholesterol': ['total cholesterol', 't.cholesterol', 'serum cholesterol', 'cholesterol'],
            'systolic_bp': ['systolic', 'systolic bp'],
            'diastolic_bp': ['diastolic', 'diastolic bp'],
            'wbc': ['white blood cell count', 'white blood cell', 'wbc count', 'wbc', 'total leucocyte count', 'tlc', 'leukocytes'],
            'rbc': ['r b c count', 'rbc count', 'rbc', 'red blood cell count', 'red blood cell', 'erythrocytes'],
            'mcv': ['mean cell volume', 'mcv'],
            'mch': ['mean cell hemoglobin', 'mean cell haemoglobin', 'mch'],
            'mchc': ['mean cell hb concentration', 'mean cell haemoglobin concentration', 'mchc'],
            'hematocrit': ['hematocrit', 'haematocrit', 'pcv'],
            'platelets': ['platelet count', 'platelets', 'plt'],
            'lymphocytes': ['lymphocytes', 'lymph'],
            'rdw_sd': ['rdw sd', 'rdw-sd'],
            'rdw_cv': ['rdw cv', 'rdw-cv'],
            'creatinine': ['serum creatinine', 's.creatinine', 'creatinine', 'creat'],
            'urea': ['blood urea nitrogen', 'blood urea', 'bun', 'urea'],
            'uric_acid': ['uric acid', 'serum uric acid', 's.uric acid'],
        }

    # ─── Image pre-processing for speed & high accuracy ───────────────────────
    def preprocess(self, img: Image.Image) -> Image.Image:
        # Resize high-res images to max width 1600 for 10x faster OCR
        max_dim = 1600
        w, h = img.size
        if w > max_dim or h > max_dim:
            if w > h:
                new_w = max_dim
                new_h = int(h * (max_dim / w))
            else:
                new_h = max_dim
                new_w = int(w * (max_dim / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Convert to grayscale
        return img.convert('L')

    # ─── OCR from image file ─────────────────────────────────────────────────
    def extract_from_image(self, filepath: str) -> str:
        try:
            img = Image.open(filepath)
            img = self.preprocess(img)
            config = '--psm 6 --oem 3'
            return pytesseract.image_to_string(img, config=config)
        except Exception as exc:
            print(f"[OCR] Image extraction error: {exc}")
            return ""

    # ─── OCR from PDF ────────────────────────────────────────────────────────
    def extract_from_pdf(self, filepath: str) -> str:
        # Attempt 1: Direct text stream extraction via pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            text = text.strip()
            if len(text) > 50:
                print(f"[OCR] Extracted {len(text)} characters of text directly using pypdf")
                return text
        except Exception as exc:
            print(f"[OCR] pypdf direct text extraction error: {exc}")

        # Attempt 2: Extract embedded images via pypdf
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(filepath)
            texts = []
            for i, page in enumerate(reader.pages):
                for img_file in page.images:
                    try:
                        img = Image.open(io.BytesIO(img_file.data))
                        img = self.preprocess(img)
                        txt = pytesseract.image_to_string(img, config='--psm 6 --oem 3')
                        if txt:
                            texts.append(txt)
                    except Exception as e:
                        print(f"[OCR] Failed to OCR embedded image: {e}")
            combined = "\n".join(texts).strip()
            if len(combined) > 10:
                return combined
        except Exception as exc:
            print(f"[OCR] pypdf embedded image extraction error: {exc}")

        # Attempt 3: pdf2image fallback
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(filepath, dpi=150)
            texts = []
            for page in pages:
                page = self.preprocess(page)
                texts.append(pytesseract.image_to_string(page, config='--psm 6 --oem 3'))
            return "\n".join(texts)
        except Exception as exc:
            print(f"[OCR] pdf2image fallback error: {exc}")
            return ""

    # ─── Public entry point ──────────────────────────────────────────────────
    def extract(self, filepath: str) -> dict:
        ext = os.path.splitext(filepath)[1].lower()
        text = self.extract_from_pdf(filepath) if ext == '.pdf' else self.extract_from_image(filepath)
        values = self.parse_values(text)
        print(f"[OCR] Extracted raw text length: {len(text)} chars")
        print(f"[OCR] Detected values: {values}")
        return values

    # ─── Universal Line-by-Line Table Parser ──────────────────────────────────
    def parse_values(self, text: str) -> dict:
        extracted = {}
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for param, keywords in self.PARAM_KEYWORDS.items():
            for line in lines:
                line_lower = line.lower()
                # Check if any keyword matches this line
                matched_kw = None
                for kw in keywords:
                    if kw in line_lower:
                        matched_kw = kw
                        break
                
                if matched_kw:
                    # Find all numbers on this line after the matched keyword
                    kw_pos = line_lower.find(matched_kw)
                    after_kw = line[kw_pos + len(matched_kw):]
                    
                    # Extract numeric tokens (integers or decimals)
                    nums = re.findall(r'\b\d+(?:\.\d+)?\b', after_kw)
                    
                    # Ignore "NA", reference ranges, or empty tokens
                    valid_nums = []
                    for n in nums:
                        try:
                            v = float(n)
                            valid_nums.append(v)
                        except ValueError:
                            pass
                    
                    if valid_nums:
                        # The first valid numeric token on the line is the test result
                        extracted[param] = valid_nums[0]
                        break

        return extracted
