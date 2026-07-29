class OfflineTranslator:
    """
    Multi-Lingual Regional Language Translation Engine for MediLensAI.
    Supports Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, and English.
    Completely offline — no internet or cloud APIs required.
    """

    LANGUAGES = {
        'en': 'English',
        'ta': 'தமிழ் (Tamil)',
        'hi': 'हिंदी (Hindi)',
        'te': 'తెలుగు (Telugu)',
        'kn': 'ಕನ್ನಡ (Kannada)',
        'ml': 'മലയാളം (Malayalam)',
        'bn': 'বাংলা (Bengali)'
    }

    SUMMARY_TEMPLATES = {
        'ta': "{patient_name} அவர்களின் சுகாதார அறிக்கை சுருக்கம். வயது {patient_age}, {patient_gender}. ஒட்டுமொத்த இடர்நிலை: {overall_risk_level}. {abnormal_count} அளவுக்கூறுகள் சிறப்பு கவனம் தேவைப்படுகின்றன. தயவுசெய்து உங்கள் மருத்துவரை அணுகவும்.",
        'hi': "{patient_name} की स्वास्थ्य रिपोर्ट का सारांश। आयु {patient_age}, {patient_gender}। समग्र जोखिम स्तर: {overall_risk_level}। {abnormal_count} मापदंडों पर ध्यान देने की आवश्यकता है। कृपया अपने डॉक्टर से परामर्श लें।",
        'te': "{patient_name} యొక్క ఆరోగ్య నివేదిక సారాంశం. వయస్సు {patient_age}, {patient_gender}. మొత్తం ప్రమాద స్థాయి: {overall_risk_level}. {abnormal_count} పారామితులపై దృష్టి పెట్టాలి. దయచేసి మీ వైద్యుడిని సంప్రదించండి.",
        'kn': "{patient_name} ಅವರ ಆರೋಗ್ಯ ವರದಿ ಸಾರಾಂಶ. ವಯಸ್ಸು {patient_age}, {patient_gender}. ಒಟ್ಟು ಅಪಾಯದ ಮಟ್ಟ: {overall_risk_level}. {abnormal_count} ನಿಯತಾಂಕಗಳ ಬಗ್ಗೆ ಕಾಳಜಿ ಅಗತ್ಯವಿದೆ. ದಯವಿಟ್ಟು ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        'ml': "{patient_name} യുടെ ആരോഗ്യ റിപ്പോർട്ട് ചുരുക്കം. പ്രായം {patient_age}, {patient_gender}. മൊത്തത്തിലുള്ള അപകടസാധ്യത: {overall_risk_level}. {abnormal_count} പാരാമീറ്ററുകൾ ശ്രദ്ധിക്കേണ്ടതാണ്. ദയവായി ഡോക്ടറെ കാണുക.",
        'bn': "{patient_name} এর স্বাস্থ্য রিপোর্টের সারসংক্ষেপ। বয়স {patient_age}, {patient_gender}। সার্বিক ঝুঁকির মাত্রা: {overall_risk_level}। {abnormal_count} টি বিষয়ে বিশেষ নজর দেওয়া প্রয়োজন। চিকিৎসকের পরামর্শ নিন।"
    }

    TRANSLATIONS = {
        'ta': {
            'Hemoglobin': 'ஹெமோகுளோபின்',
            'Blood Sugar (Fasting)': 'இரத்த சர்க்கரை அளவு',
            'Total Cholesterol': 'கொலஸ்ட்ரால் அளவு',
            'Systolic Blood Pressure': 'சுருங்கு இரத்த அழுத்தம்',
            'Diastolic Blood Pressure': 'விரிவு இரத்த அழுத்தம்',
            'Creatinine': 'கிரியேட்டினின்',
            'WBC Count': 'வெள்ளை இரத்த அணுக்கள்',
            'RBC Count': 'சிவப்பு இரத்த அணுக்கள்',
            'Blood Urea': 'இரத்த உரியா',
            'Uric Acid': 'யூரிக் அமிலம்',
            'Normal': 'சாதாரண நிலை',
            'Low': 'குறைந்த நிலை',
            'Critical Low': 'மிகக் குறைந்த நிலை',
            'Moderate': 'மிதமான எச்சரிக்கை',
            'High': 'அதிக நிலை',
            'Critical': 'மிக ஆபத்தான நிலை',
            'Not Detected': 'கண்டறியப்படவில்லை',
            'Overall Health Risk': 'மொத்த ஆரோக்கிய இடர்நிலை',
        },
        'hi': {
            'Hemoglobin': 'हीमोग्लोबिन',
            'Blood Sugar (Fasting)': 'ब्लड शुगर',
            'Total Cholesterol': 'कुल कोलेस्ट्रॉल',
            'Systolic Blood Pressure': 'सिस्टोलिक रक्तचाप',
            'Diastolic Blood Pressure': 'डायस्टोलिक रक्तचाप',
            'Creatinine': 'क्रिएटिनिन',
            'WBC Count': 'श्वेत रक्त कोशिकाएं',
            'RBC Count': 'लाल रक्त कोशिकाएं',
            'Blood Urea': 'ब्लड यूरिया',
            'Uric Acid': 'यूरिक एसिड',
            'Normal': 'सामान्य',
            'Low': 'निम्न स्तर',
            'Critical Low': 'गंभीर रूप से कम',
            'Moderate': 'मध्यम जोखिम',
            'High': 'उच्च स्तर',
            'Critical': 'गंभीर जोखिम',
            'Not Detected': 'पहचाना नहीं गया',
            'Overall Health Risk': 'समग्र स्वास्थ्य जोखिम',
        },
        'te': {
            'Hemoglobin': 'హీమోగ్లోబిన్',
            'Blood Sugar (Fasting)': 'బ్లడ్ షుగర్',
            'Total Cholesterol': 'కొలెస్ట్రాల్',
            'Systolic Blood Pressure': 'సిస్టోలిక్ బ్లడ్ ప్రెజర్',
            'Diastolic Blood Pressure': 'డయాస్టోలిక్ బ్లడ్ ప్రెజర్',
            'Creatinine': 'క్రియాటినిన్',
            'Normal': 'సాధారణం',
            'Low': 'తక్కువ',
            'High': 'ఎక్కువ',
            'Critical': 'తీవ్రమైనది',
        },
        'kn': {
            'Hemoglobin': 'ಹಿಮೋಗ್ಲೋಬಿನ್',
            'Blood Sugar (Fasting)': 'ರಕ್ತದ ಸಕ್ಕರೆ',
            'Total Cholesterol': 'ಕೊಲೆಸ್ಟ್ರಾಲ್',
            'Normal': 'ಸಾಮಾನ್ಯ',
            'Low': 'ಕಡಿಮೆ',
            'High': 'ಹೆಚ್ಚು',
            'Critical': 'ಅಪಾಯಕಾರಿ',
        },
        'ml': {
            'Hemoglobin': 'ഹീമോഗ്ലോബിൻ',
            'Blood Sugar (Fasting)': 'രക്തത്തിലെ പഞ്ചസാര',
            'Total Cholesterol': 'കൊളസ്ട്രോൾ',
            'Normal': 'സാധാരണ',
            'Low': 'കുറഞ്ഞ അളവ്',
            'High': 'ഉയർന്ന അളവ്',
            'Critical': 'ഗുരുതരം',
        },
        'bn': {
            'Hemoglobin': 'হিমোগ্লোবিন',
            'Blood Sugar (Fasting)': 'রক্তের শর্করা',
            'Total Cholesterol': 'কোলেস্টেরল',
            'Normal': 'স্বাভাবিক',
            'Low': 'কম',
            'High': 'উচ্চ',
            'Critical': 'গুরুতর',
        }
    }

    def translate_text(self, text: str, lang: str = 'en') -> str:
        if lang == 'en' or lang not in self.TRANSLATIONS:
            return text
        
        dictionary = self.TRANSLATIONS[lang]
        if text in dictionary:
            return dictionary[text]
            
        translated = text
        for en_word, reg_word in dictionary.items():
            translated = translated.replace(en_word, reg_word)
        return translated

    def get_translated_summary(self, report_dict: dict, parameters_list: list, lang: str = 'en') -> str:
        if lang == 'en' or lang not in self.SUMMARY_TEMPLATES:
            # Standard English summary
            r = report_dict
            detected = [p for p in parameters_list if p.get('value') is not None]
            abnormal = [p for p in detected if p.get('risk_level') not in ('Normal', 'Not Detected')]
            
            text = f"Health report summary for {r.get('patient_name')}. "
            text += f"Age {r.get('patient_age')}, {r.get('patient_gender')}. "
            text += f"Overall risk level: {r.get('overall_risk_level')}. "
            if not detected:
                text += "No medical parameters were detected."
            elif not abnormal:
                text += f"All {len(detected)} detected parameters are within the normal range."
            else:
                text += f"{len(abnormal)} parameter(s) require attention. Please follow health recommendations."
            return text

        r = report_dict
        detected = [p for p in parameters_list if p.get('value') is not None]
        abnormal = [p for p in detected if p.get('risk_level') not in ('Normal', 'Not Detected')]
        
        tpl = self.SUMMARY_TEMPLATES[lang]
        overall_risk_translated = self.translate_text(r.get('overall_risk_level', 'Normal'), lang=lang)
        
        return tpl.format(
            patient_name=r.get('patient_name', 'Patient'),
            patient_age=r.get('patient_age', 'N/A'),
            patient_gender=r.get('patient_gender', 'N/A'),
            overall_risk_level=overall_risk_translated,
            abnormal_count=len(abnormal)
        )
