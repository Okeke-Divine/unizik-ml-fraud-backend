# unizik-ml-fraud-backend/app/model_engine.py

import os
import math
import joblib
import numpy as np
from app.config import Config

class FraudDetectionEngine:
    def __init__(self):
        self.model = None
        self.feature_columns = [
            'device_student_count_24h',
            'page_dwell_time_seconds',
            'is_high_risk_asn',
            'failed_attempts_1h',
            'session_hardware_mismatch',
            'is_off_peak_hour'
        ]
        self.load_model()

    def load_model( -> bool:
        """Loads the serialized decision tree binary from disk into RAM."""
        if os.path.exists(Config.MODEL_PATH):
            try:
                self.model = joblib.load(Config.MODEL_PATH)
                return True
            except Exception as e:
                print(f"[FATAL ERROR] Failed to load model binary: {e}")
                return False
        return False

    def _safe_float(self, value, default: float, min_val: float = None, max_val: float = None) -> float:
        """
        Ruthlessly sanitizes and casts incoming JSON variables.
        Prevents HTTP 500 crashes from nulls, strings, NaNs, and clamps Out-of-Distribution (OOD) exploits.
        """
        if value is None or value == "":
            return default
        try:
            val = float(value)
            # Catch Python NaN or Infinity strings
            if math.isnan(val) or math.isinf(val):
                return default
            # Clamp boundaries to prevent Decision Tree OOD blindspot exploits (like dwell=9999s)
            if min_val is not None and val < min_val:
                val = min_val
            if max_val is not None and val > max_val:
                val = max_val
            return val
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default: int, min_val: int = None, max_val: int = None) -> int:
        """Sanitizes and casts integer variables safely."""
        val = self._safe_float(value, float(default), float(min_val) if min_val is not None else None, float(max_val) if max_val is not None else None)
        return int(val)

    def extract_features(self, payload: dict) -> list:
        """
        Extracts feature vectors with defensive type checking and OOD boundary clipping.
        """
        # Clamp velocity between 0 and 150 accounts
        device_count = self._safe_int(payload.get('device_student_count_24h'), default=1, min_val=0, max_val=150)
        
        # Clamp dwell time between 0.1s and 180.0s to prevent artificial sleep bypass attacks
        dwell_time = self._safe_float(payload.get('page_dwell_time_seconds'), default=65.0, min_val=0.1, max_val=180.0)
        
        # Binary flags must be strictly 0 or 1
        high_risk_asn = 1 if str(payload.get('is_high_risk_asn', 0)).lower() in ['1', 'true', 'yes'] else 0
        
        # Clamp failed attempts between 0 and 20
        failed_attempts = self._safe_int(payload.get('failed_attempts_1h'), default=0, min_val=0, max_val=20)
        
        hardware_mismatch = 1 if str(payload.get('session_hardware_mismatch', 0)).lower() in ['1', 'true', 'yes'] else 0
        off_peak = 1 if str(payload.get('is_off_peak_hour', 0)).lower() in ['1', 'true', 'yes'] else 0

        return [device_count, dwell_time, high_risk_asn, failed_attempts, hardware_mismatch, off_peak]

    def _generate_explanation(self, features: list, prediction: int) -> str:
        """Generates white-box audit explanations for system administrators and thesis defense."""
        device_count, dwell_time, asn, fails, mismatch, off_peak = features

        if prediction == 0:
            return "Transaction parameters align with normal campus student behavioral distributions."

        reasons = []
        if device_count > 3:
            reasons.append(f"High device-to-student velocity (>3 distinct accounts in 24h: recorded {device_count})")
        if dwell_time < 6.0:
            reasons.append(f"Abnormal form completion speed (<6 seconds dwell time: recorded {dwell_time}s)")
        if asn == 1:
            reasons.append("IP routing originates from an anonymized or datacenter ASN")
        if fails >= 3:
            reasons.append(f"High card-testing failure rate detected in the last hour ({fails} failures)")
        if mismatch == 1:
            reasons.append("Hardware fingerprint mismatch against initial login session")
        if off_peak == 1 and (fails >= 2 or asn == 1):
            reasons.append("High-risk execution timing during off-peak campus hours (1 AM - 4:30 AM WAT)")

        if not reasons:
            reasons.append("Complex multi-variable decision boundary violation detected by Gini impurity scaling")

        return "BLOCKED BY AI: " + "; ".join(reasons) + "."

    def predict(self, payload: dict) -> dict:
        """Executes live classification and returns structured forensic JSON output."""
        if not self.model:
            if not self.load_model():
                return {
                    "status": "error",
                    "message": "AI model binary unavailable. Please execute train_model.py first."
                }

        try:
            features = self.extract_features(payload)
            feature_array = np.array([features])

            # Execute inference
            prediction = int(self.model.predict(feature_array)[0])
            probabilities = self.model.predict_proba(feature_array)[0]
            confidence = float(probabilities[prediction])

            verdict = "FRAUDULENT" if prediction == 1 else "LEGITIMATE"
            explanation = self._generate_explanation(features, prediction)

            return {
                "status": "success",
                "verdict": verdict,
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "explanation": explanation
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Inference pipeline error: {str(e)}"
            }