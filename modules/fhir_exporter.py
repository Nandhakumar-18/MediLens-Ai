import json
from datetime import datetime

class FHIRExporter:
    """
    Enterprise Data Security & EMR Standard Compliance Exporter.
    Exports medical report findings into official HL7 FHIR R4 JSON Bundle format.
    """

    def export_bundle(self, report: dict, parameters: list) -> dict:
        report_id = str(report.get('id', 1))
        patient_name = report.get('patient_name', 'Anonymous')
        upload_date = report.get('upload_date', datetime.utcnow().isoformat())

        # FHIR DiagnosticReport Resource
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entry": [
                {
                    "fullUrl": f"urn:uuid:patient-{report_id}",
                    "resource": {
                        "resourceType": "Patient",
                        "id": f"patient-{report_id}",
                        "name": [{"text": patient_name}],
                        "gender": str(report.get('patient_gender', 'unknown')).lower()
                    }
                },
                {
                    "fullUrl": f"urn:uuid:report-{report_id}",
                    "resource": {
                        "resourceType": "DiagnosticReport",
                        "id": f"report-{report_id}",
                        "status": "final",
                        "code": {
                            "text": "MediLensAI Offline Diagnostic Intelligence Report"
                        },
                        "subject": {"reference": f"Patient/patient-{report_id}"},
                        "effectiveDateTime": upload_date,
                        "conclusion": f"Overall Risk Level: {report.get('overall_risk_level', 'Normal')} (Score: {report.get('overall_risk_score', 0)}/4.0)"
                    }
                }
            ]
        }

        # Add FHIR Observation entries for each parameter
        for p in parameters:
            if p.get('value') is not None:
                obs_entry = {
                    "fullUrl": f"urn:uuid:observation-{p.get('id', p.get('name'))}",
                    "resource": {
                        "resourceType": "Observation",
                        "id": f"obs-{p.get('id', p.get('name'))}",
                        "status": "final",
                        "code": {"text": p.get('display_name', p.get('name'))},
                        "subject": {"reference": f"Patient/patient-{report_id}"},
                        "valueQuantity": {
                            "value": p.get('value'),
                            "unit": p.get('unit', '')
                        },
                        "referenceRange": [
                            {
                                "low": {"value": p.get('normal_min', 0)},
                                "high": {"value": p.get('normal_max', 100)}
                            }
                        ],
                        "interpretation": [
                            {
                                "text": p.get('risk_level', 'Normal')
                            }
                        ]
                    }
                }
                bundle["entry"].append(obs_entry)

        return bundle
