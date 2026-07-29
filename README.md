# 🩺 MediLensAI — Offline Health Intelligence System

> **A 100% Offline, Edge-AI Powered Health Intelligence & Early Warning Platform for Medical Lab Reports, ECG Waveforms, Chest X-Rays, and Dermatology Diagnostics.**

---

## 📌 Project Description

**MediLensAI** is an advanced, fully offline medical diagnostic and health intelligence web platform engineered for rural health centers, primary healthcare clinics (PHCs), mobile medical units, and privacy-conscious users. Operating with **0% cloud dependency, 0% paid web APIs, and 0% internet connection**, MediLensAI transforms raw printed medical lab reports, ECG traces, chest radiographs, and skin lesion photos into actionable clinical insights.

The platform provides automated biomarkers extraction, reference-range risk stratification, multi-modal computer vision analysis, personalized medical recommendations, HL7 FHIR R4 EMR exports, and innovative offline security protocols (Device SIM SMS & RFC 6238 TOTP QR Authenticator).

---

## 🛠️ Technology Stack

| Component | Technologies & Libraries Used |
|---|---|
| **Core Web Framework** | Python 3.14, Flask, WSGI |
| **Database Engine** | SQLite3 (With Schema Auto-Migrations & Indexing) |
| **Optical Character Recognition (OCR)** | Tesseract OCR, PyTesseract, OpenCV, Pillow (PIL) |
| **Computer Vision Engine** | OpenCV, NumPy, SciPy (Signal Processing & Image Analysis) |
| **Frontend & Styling** | Vanilla HTML5, Custom CSS3 (Dark Glassmorphism Design System) |
| **Data Visualization** | Chart.js (Local Bundle — Radar Charts, Gauges, Bar & Doughnut Charts) |
| **Speech & Audio** | Native Web Speech API (`SpeechSynthesis`) |
| **Offline Security & TOTP** | Python `hmac`, `hashlib`, `qrcode` (RFC 6238 Standard) |
| **EMR Interoperability** | HL7 FHIR R4 JSON Exporter |

---

## ✨ Key Features

1. **100% Offline Edge Operation**: Requires zero cloud API subscriptions (Twilio, OpenAI, Google Cloud). Operates inside airplane mode, basements, or remote PHCs.
2. **Multi-Modal Diagnostic Support**:
   - **Blood / Lab Test Reports**: Extracted via Tesseract OCR (Hb, Glucose, Cholesterol, BP, Creatinine, WBC, RBC, Urea, Uric Acid).
   - **ECG Waveforms**: Computer vision QRS duration & rhythm irregularity analysis.
   - **Chest X-Rays**: Pulmonary infiltrate radiodensity & cardiothoracic ratio (CTR) measurement.
   - **Dermatology**: Dermoscopy ABCD asymmetry & border regularity scoring.
3. **Tiered User Accounts & Daily Quotas**:
   - **Patient Accounts**: Capped at 5 report uploads per calendar day.
   - **Doctor / Medical Organization Accounts**: Unlimited uploads for high-volume clinic workflows.
4. **Data Isolation & Security**: Per-user directory isolation (`static/uploads/user_<id>/`) and row-level database authorization.
5. **Persistent 30-Day Device Auto-Login**: Remembers authorized laptops/phones seamlessly using persistent secure session cookies.
6. **Dual Offline Password Recovery**:
   - **Device SIM SMS OTP**: Dispatches 6-digit text via native Android `SmsManager` or USB SIM Dongle serial AT commands.
   - **Offline QR Authenticator**: RFC 6238 TOTP compatible with Google Authenticator, Microsoft Authenticator, Authy, and Apple Keychain (0% internet required).
7. **HL7 FHIR R4 Export**: Generates compliant JSON EMR bundles for seamless hospital software integration.

---

## 🧩 Basic Modules

- `app.py`: Main Flask application server, route controllers, session security middleware, and file handler.
- `database/db.py`: SQLite abstraction layer handling schema migrations, user authentication, report persistence, and quota enforcement.
- `modules/ocr_extractor.py`: Image preprocessing (grayscale, thresholding, denoising) and regex biomarker extraction.
- `modules/risk_predictor.py`: Clinical reference range mapping and weighted 4-point health risk scoring.
- `modules/recommendation_engine.py`: Rule-based clinical advice generator for Medical, Diet, Exercise, and Lifestyle categories.
- `modules/alert_system.py`: Real-time health warning trigger and local SMS log simulator.
- `modules/computer_vision.py`: Waveform signal processor and medical image radiodensity analyzer.
- `modules/totp_authenticator.py`: RFC 6238 TOTP secret generator and SVG QR code renderer.
- `modules/fhir_exporter.py`: Standard HL7 FHIR R4 JSON Bundle generator.

---

## 🏗️ System Architecture

```text
+-----------------------------------------------------------------------+
|                            USER INTERFACE                             |
|          Desktop Browser Workstation / Mobile Phone (PWA)             |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------+-----------------------------------+
|                           FLASK CONTROLLER                            |
|       Authentication (@login_required) | Quota & Session Manager       |
+---------+-------------------------+-------------------------+---------+
          |                         |                         |
          v                         v                         v
+---------+----------+    +---------+----------+    +---------+---------+
|  DIAGNOSTIC OCR    |    |  COMPUTER VISION   |    | OFFLINE SECURITY  |
|  Tesseract Engine  |    |  ECG / X-Ray / Skin|    | TOTP / Device SIM |
+---------+----------+    +---------+----------+    +---------+---------+
          |                         |                         |
          +-------------------------+-------------------------+
                                    |
                                    v
+-----------------------------------+-----------------------------------+
|                        LOCAL STORAGE & EMR                            |
|  SQLite3 Database (medilensai.db) | HL7 FHIR R4 Exporter | File Uploads |
+-----------------------------------------------------------------------+
```

---

## 🔄 Project Workflow

1. **User Sign In / Registration**: User creates an account specifying a unique 10-digit mobile number and role (`Patient` or `Doctor`).
2. **Report Upload**: On the Home Upload Portal, the user selects the Diagnostic Mode and uploads a PDF, PNG, JPG, or TIFF file.
3. **Automated Processing**:
   - *Lab Reports*: OCR extracts parameter values and maps them against clinical normal ranges.
   - *Medical Images*: Computer vision calculates signal features and opacity thresholds.
4. **Risk & Recommendation Generation**: Calculates overall health risk score (0 to 4) and generates targeted medical/lifestyle advice.
5. **Interactive Dashboard Display**: Renders Radar Charts, Semi-Circular Gauges, Bar Charts, Doughnut Distributions, and English Voice Readouts.
6. **FHIR Export**: Option to download HL7 FHIR R4 EMR JSON bundle for hospital integration.

---

## 🌟 Advantages

- **Zero Operating Costs**: No cloud server hosting or paid API subscription fees required.
- **Maximum Privacy**: Health data never leaves the local device storage.
- **High Reliability**: Operates continuously during power outages, network blackouts, and remote field deployments.
- **Universal Mobile Accessibility**: Runs on mobile browsers and installs as an offline Progressive Web App (PWA).

---

## 🚀 Future Enhancements

1. **Deep Learning Segmentation**: Integrate lightweight ONNX / TensorFlow Lite models directly on device for advanced multi-class tumor and lesion segmentation.
2. **BLE Hardware Wristband Pairing**: Connect Bluetooth Low Energy (BLE) vital sign wearables for continuous offline heart rate and SpO2 logging.
3. **Multi-Clinic Sync over Local Mesh**: Enable peer-to-peer Wi-Fi Direct sync between rural clinic tablets and central doctor workstations.

---

## 📝 Conclusion

**MediLensAI** proves that cutting-edge medical artificial intelligence and enterprise-grade health management do not require expensive cloud infrastructure or internet connectivity. By combining computer vision, OCR, FHIR EMR standards, and innovative offline security protocols, MediLensAI provides a self-contained, secure, and life-saving digital healthcare solution for everyone, anywhere.
