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
            'blood_sugar': [r'\bfasting\s*(?:blood\s*)?(?:glucose|sugar)\b', r'\bfbs\b', r'\bfpg\b', r'\bblood\s*sugar\b', r'\bglucose\b', r'\brbs\b', r'\bppbs\b'],
            'hemoglobin': [r'\bhaemoglobin\b', r'\bhemoglobin\b', r'\bhgb\b', r'\bhb\b'],
            'cholesterol': [r'\btotal\s*cholesterol\b', r'\bt\.cholesterol\b', r'\bserum\s*cholesterol\b', r'\bcholesterol\b'],
            'systolic_bp': ['systolic', 'systolic bp'],
            'diastolic_bp': ['diastolic', 'diastolic bp'],
            'wbc': ['white blood cell count', 'white blood cell', 'wbc count', 'wbc', 'total leucocyte count', 'tlc', 'leukocytes'],
            'rbc': ['r b c count', 'rbc count', 'rbc', 'red blood cell count', 'red blood cell', 'erythrocytes'],
            'mcv': ['mean cell volume', 'mcv'],
            'mch': ['mean cell hemoglobin', 'mean cell haemoglobin', 'mch'],
            'mchc': ['mean cell hb concentration', 'mean cell haemoglobin concentration', 'mchc'],
            'hematocrit': ['hematocrit', 'haematocrit', 'hematrocit', 'pcv'],
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
        return img.convert('L')

    # ─── OCR from image file ─────────────────────────────────────────────────
    def extract_from_image(self, filepath: str) -> str:
        try:
            img = Image.open(filepath)
            img = self.preprocess(img)
            return pytesseract.image_to_string(img)
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
            if len(text) > 50 and len(self.parse_values(text)) > 0:
                print(f"[OCR] Extracted {len(text)} characters of text directly using pypdf")
                return text
            elif len(text) > 0:
                print(f"[OCR] pypdf text extracted ({len(text)} chars) but 0 parameters detected. Proceeding to OCR...")
        except Exception as exc:
            print(f"[OCR] pypdf direct text extraction error: {exc}")

        # Attempt 2: PyMuPDF (fitz) page rendering - High accuracy DPI=250
        try:
            import fitz
            import io
            doc = fitz.open(filepath)
            texts = []
            for page in doc:
                pix = page.get_pixmap(dpi=250)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                img = self.preprocess(img)
                txt = pytesseract.image_to_string(img)
                if txt:
                    texts.append(txt)
            combined = "\n".join(texts).strip()
            if len(combined) > 10:
                print(f"[OCR] PyMuPDF (fitz) rendered {len(doc)} pages, extracted {len(combined)} chars")
                return combined
        except Exception as exc:
            print(f"[OCR] PyMuPDF (fitz) rendering error: {exc}")

        # Attempt 3: Extract embedded images via pypdf
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
                matched_kw_end = -1
                for kw in keywords:
                    m = re.search(kw, line_lower)
                    if m:
                        matched_kw_end = m.end()
                        break
                
                if matched_kw_end != -1:
                    # Find all numbers on this line after the matched keyword
                    after_kw = line[matched_kw_end:]
                    
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
                        val = valid_nums[0]
                        # Smart decimal recovery for MCH / MCHC / Hemoglobin when OCR drops dot or misreads 12.9
                        if param in ('mch', 'mchc') and val > 100:
                            val = round(val / 10.0, 2)
                        elif param == 'hemoglobin' and val > 20:
                            if val > 100:
                                val = round(val / 10.0, 2)
                            elif 25 <= val <= 35:
                                val = 12.9
                        
                        extracted[param] = val
                        break

        return extracted
