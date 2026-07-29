import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import re
import os


class OCRExtractor:
    """
    Extracts medical parameter values from uploaded report images or PDFs
    using Tesseract OCR and regex pattern matching. Fully offline.
    """

    def __init__(self):
        # Auto-detect Tesseract on Windows
        win_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(win_path):
            pytesseract.pytesseract.tesseract_cmd = win_path

        # Regex patterns per parameter (most specific first)
        self.patterns = {
            'blood_sugar': [
                r'(?:fasting\s*(?:blood\s*)?(?:glucose|sugar)|fbs|fpg)[\s:=\-]+(\d+(?:\.\d+)?)',
                r'(?:blood\s*sugar|glucose|rbs|ppbs)[\s:=\-]+(\d+(?:\.\d+)?)',
                r'(\d{2,3})\s*mg[/\\]d[lL].*?(?:glucose|sugar|glyc)',
            ],
            'hemoglobin': [
                r'(?:haemoglobin|hemoglobin|hgb|hb)[\s:=\-]+(\d+(?:\.\d+)?)',
                r'\bhb[\s:=\-]+(\d+(?:\.\d+)?)',
            ],
            'cholesterol': [
                r'(?:total\s*cholesterol|t\.cholesterol|cholesterol\s*total|serum\s*cholesterol)[\s:=\-]+(\d+(?:\.\d+)?)',
                r'cholesterol[\s:=\-]+(\d+(?:\.\d+)?)',
            ],
            'systolic_bp': [
                r'(?:bp|blood\s*pressure|b\.p\.)[\s:=\-]+(\d{2,3})\s*/\s*\d{2,3}',
                r'systolic[\s:=\-]+(\d{2,3})',
                r'(\d{2,3})\s*/\s*\d{2,3}\s*mm\s*hg',
            ],
            'diastolic_bp': [
                r'(?:bp|blood\s*pressure|b\.p\.)[\s:=\-]+\d{2,3}\s*/\s*(\d{2,3})',
                r'diastolic[\s:=\-]+(\d{2,3})',
            ],
            'wbc': [
                r'(?:wbc|white\s*blood\s*(?:cell|corpuscle)s?|total\s*(?:leuco|leuko)cyte|tlc)[\s:=\-]+(\d[\d,]*(?:\.\d+)?)',
                r'leukocytes?[\s:=\-]+(\d[\d,]*(?:\.\d+)?)',
            ],
            'rbc': [
                r'(?:rbc|red\s*blood\s*(?:cell|corpuscle)s?|erythrocytes?)[\s:=\-]+(\d+(?:\.\d+)?)',
            ],
            'creatinine': [
                r'(?:s\.?\s*creatinine|serum\s*creatinine|creat(?:inine)?)[\s:=\-]+(\d+(?:\.\d+)?)',
            ],
            'urea': [
                r'(?:blood\s*urea\s*nitrogen|bun|blood\s*urea|urea)[\s:=\-]+(\d+(?:\.\d+)?)',
            ],
            'uric_acid': [
                r'(?:uric\s*acid|s\.?\s*uric\s*acid|serum\s*uric)[\s:=\-]+(\d+(?:\.\d+)?)',
            ],
        }

    # ─── Image pre-processing ────────────────────────────────────────────────
    def preprocess(self, img: Image.Image) -> Image.Image:
        # Grayscale improves OCR speed and accuracy without distorting clean fonts
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

    # ─── OCR from PDF (converted page-by-page) ───────────────────────────────
    def extract_from_pdf(self, filepath: str) -> str:
        # First attempt: Try extracting text directly using pypdf (no poppler/external tools needed)
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
            print(f"[OCR] pypdf text extraction error: {exc}")

        # Second attempt: Try extracting embedded images from PDF pages using pypdf (no poppler/external tools needed)
        print("[OCR] Direct text extraction yielded nothing. Trying to extract embedded images via pypdf...")
        try:
            from pypdf import PdfReader
            import io
            from PIL import Image
            reader = PdfReader(filepath)
            texts = []
            for i, page in enumerate(reader.pages):
                for img_file in page.images:
                    try:
                        img = Image.open(io.BytesIO(img_file.data))
                        img = self.preprocess(img)
                        config = '--psm 6 --oem 3'
                        txt = pytesseract.image_to_string(img, config=config)
                        if txt:
                            texts.append(txt)
                    except Exception as e:
                        print(f"[OCR] Failed to OCR embedded image {img_file.name} on page {i}: {e}")
            
            combined_text = "\n".join(texts).strip()
            if len(combined_text) > 10:
                print(f"[OCR] Successfully extracted {len(combined_text)} characters from embedded images via pypdf")
                return combined_text
        except Exception as exc:
            print(f"[OCR] pypdf embedded image extraction error: {exc}")

        # Third attempt: Fallback to OCR via pdf2image (requires Poppler)
        print("[OCR] Pure Python image extraction yielded nothing. Falling back to pdf2image (requires Poppler)...")
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(filepath, dpi=300)
            texts = []
            for page in pages:
                page = self.preprocess(page)
                texts.append(pytesseract.image_to_string(page, config='--psm 6 --oem 3'))
            return "\n".join(texts)
        except Exception as exc:
            print(f"[OCR] PDF OCR extraction error: {exc}")
            return ""

    # ─── Public entry point ──────────────────────────────────────────────────
    def extract(self, filepath: str) -> dict:
        ext = os.path.splitext(filepath)[1].lower()
        text = self.extract_from_pdf(filepath) if ext == '.pdf' else self.extract_from_image(filepath)
        values = self.parse_values(text)
        print(f"[OCR] Extracted raw text length: {len(text)} chars")
        print(f"[OCR] Detected values: {values}")
        return values

    # ─── Regex value parser ──────────────────────────────────────────────────
    def parse_values(self, text: str) -> dict:
        extracted = {}
        text_lower = text.lower()
        for param, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    try:
                        val = float(match.group(1).replace(',', ''))
                        extracted[param] = val
                        break
                    except (ValueError, AttributeError):
                        continue
        return extracted
