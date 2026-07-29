# Use official lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Tesseract OCR and system libraries required for Pillow/OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt-get/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask==3.0.3 \
    pytesseract==0.3.10 \
    Pillow==10.3.0 \
    pypdf==4.2.0 \
    fpdf2==2.7.9 \
    waitress==3.0.0 \
    qrcode==7.4.2

# Copy application source code
COPY . /app

# Expose port 5000
EXPOSE 5000

# Start application using Waitress production WSGI server
CMD ["python", "-c", "from waitress import serve; from app import app, db; db.init_db(); serve(app, host='0.0.0.0', port=5000)"]
