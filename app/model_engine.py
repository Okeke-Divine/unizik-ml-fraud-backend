# unizik-ml-fraud-backend/app/model_engine.py

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from app.config import Config

class FraudDetectionEngine:
    def __init__(self):
        self.model_path = Config.MODEL_PATH
        self.model = None
        self.feature_names = [
            'device_student_count_24h',
            'page_dwell_time_seconds',
            'is_high_risk_asn',
            'failed_attempts_1h',
            'session_hardware_mismatch',
            'is_off_peak_hour'
        ]

    def load_model(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        try:
            self.model = joblib.load(self.model_path)
            return True
        except Exception as error:
            print(f"Error loading model binary: {error}")
            return False

    def predict(self, payload: dict) -> dict:
        if self.model is None:
            loaded = self.load_model()
            if not loaded:
                return {
                    "status": "error",
                    "message": "Decision Tree model binary not found. Train the model before executing predictions.",
                    "prediction": None
                }

        try:
            # Extract features in strict mathematical order
            features = [
                float(payload.get('device_student_count_24h', 0)),
                float(payload.get('page_dwell_time_seconds', 0.0)),
                int(payload.get('is_high_risk_asn', 0)),
                int(payload.get('failed_attempts_1h', 0)),
                int(payload.get('session_hardware_mismatch', 0)),
                int(payload.get('is_off_peak_hour', 0))
            ]

            input_array = np.array([features])
            input_df = pd.DataFrame(input_array, columns=self.feature_names)

            # Execute binary classification (0 = Legitimate, 1 = Fraudulent)
            prediction_class = int(self.model.predict(input_df)[0])
            class_probabilities = self.model.predict_proba(input_df)[0]
            confidence_score = float(class_probabilities[prediction_class])

            # White-Box Diagnostic Output
            verdict = "FRAUDULENT" if prediction_class == 1 else "LEGITIMATE"
            explanation = self._generate_explanation(prediction_class, payload)

            return {
                "status": "success",
                "prediction": prediction_class,
                "verdict": verdict,
                "confidence": round(confidence_score, 4),
                "explanation": explanation
            }
        except Exception as error:
            return {
                "status": "error",
                "message": f"Inference calculation failure: {str(error)}",
                "prediction": None
            }

    def _generate_explanation(self, prediction_class: int, payload: dict) -> str:
        if prediction_class == 0:
            return "Transaction parameters align with normal campus student behavioral distributions."
        
        reasons = []
        if float(payload.get('device_student_count_24h', 0)) > 3:
            reasons.append("High device-to-student velocity (>3 distinct accounts in 24h)")
        if float(payload.get('page_dwell_time_seconds', 0.0)) < 6.0:
            reasons.append("Abnormal form completion speed (<6 seconds dwell time)")
        if int(payload.get('is_high_risk_asn', 0)) == 1:
            reasons.append("IP routing originates from an anonymized or datacenter ASN")
        if int(payload.get('failed_attempts_1h', 0)) >= 3:
            reasons.append("High card-testing failure rate detected in the last hour")
        if int(payload.get('session_hardware_mismatch', 0)) == 1:
            reasons.append("Hardware fingerprint mismatch against initial login session")
            
        if not reasons:
            return "Flagged by non-linear multi-variable decision boundary threshold."
            
        return "BLOCKED BY AI: " + "; ".join(reasons) + "."