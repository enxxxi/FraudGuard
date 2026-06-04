import os
from datetime import datetime, timezone
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="FraudGuard ML Service", version="0.1.0")

# Load model and feature columns at startup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "fraud_model.pkl")
COLS_PATH = os.path.join(BASE_DIR, "feature_columns.pkl")

try:
    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(COLS_PATH)
    print("Model and features loaded successfully.")
except Exception as e:
    print(f"Error loading model or features: {e}")
    model = None
    feature_cols = None

class Transaction(BaseModel):
    amount: float = Field(default=0, ge=0)
    currency: str | None = "MYR"
    transactionType: str | None = "UNKNOWN"
    transactionTime: str | None = None
    merchant: str | None = "Unknown Merchant"
    location: str | None = "Unknown"
    direction: str | None = "UNKNOWN"
    referenceId: str | None = None
    extractionWarnings: list[str] = Field(default_factory=list)

class PredictionRequest(BaseModel):
    transaction: Transaction
    context: dict[str, Any] = Field(default_factory=dict)

def parse_time(time_str: str | None) -> datetime:
    if not time_str:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)

def is_late_night(dt: datetime) -> bool:
    return 0 <= dt.hour < 5

def add_factor(factors: list[dict[str, Any]], code: str, reason: str, weight: float, field: str | None = None, observed_value: Any = None) -> float:
    factor = {
        "code": code,
        "reason": reason,
        "weight": weight
    }
    if field is not None:
        factor["field"] = field
    if observed_value is not None:
        factor["observedValue"] = observed_value
    factors.append(factor)
    return weight

def risk_level(probability: float) -> str:
    if probability >= 0.7:
        return "HIGH"
    if probability >= 0.4:
        return "MEDIUM"
    return "LOW"

def check_suspicious_factors(transaction: Transaction, dt: datetime) -> list[dict[str, Any]]:
    factors = []
    
    # Amount rules
    if transaction.amount >= 5000:
        add_factor(
            factors,
            "UNUSUALLY_HIGH_AMOUNT",
            f"Transaction amount of {transaction.amount} is above the high-risk threshold.",
            0.35,
            field="amount",
            observed_value=transaction.amount
        )
    elif transaction.amount >= 1500:
        add_factor(
            factors,
            "ELEVATED_AMOUNT",
            f"Transaction amount of {transaction.amount} is above the medium-risk threshold.",
            0.18,
            field="amount",
            observed_value=transaction.amount
        )
        
    # Transaction type
    txn_type = (transaction.transactionType or "").upper()
    if txn_type in {"ATM_WITHDRAWAL", "ONLINE_PURCHASE", "FUND_TRANSFER"}:
        add_factor(
            factors,
            "RISKY_TRANSACTION_TYPE",
            f"Transaction type {txn_type} has elevated fraud exposure.",
            0.12,
            field="transactionType",
            observed_value=txn_type
        )
        
    # Merchant name
    merchant = (transaction.merchant or "").lower()
    if any(term in merchant for term in ("crypto", "gift card", "unknown", "betting", "gambling", "offshore", "forex")):
        add_factor(
            factors,
            "UNUSUAL_MERCHANT",
            "Merchant name matches a suspicious or unusual merchant pattern.",
            0.16,
            field="merchant",
            observed_value=transaction.merchant or "Unknown Merchant"
        )
        
    # Location
    location = (transaction.location or "").lower()
    if any(term in location for term in ("unknown", "offshore", "high risk", "nigeria", "russia")):
        add_factor(
            factors,
            "SUSPICIOUS_LOCATION",
            "Location is unknown or has been marked as high risk.",
            0.16,
            field="location",
            observed_value=transaction.location or "Unknown"
        )
        
    # Late night
    if is_late_night(dt):
        add_factor(
            factors,
            "LATE_NIGHT_TRANSACTION",
            "Transaction occurred between midnight and 5 AM.",
            0.18,
            field="transactionTime",
            observed_value=transaction.transactionTime
        )
        
    # Warnings
    if transaction.extractionWarnings:
        add_factor(
            factors,
            "LOW_EXTRACTION_CONFIDENCE",
            f"{len(transaction.extractionWarnings)} extraction warning(s) were produced.",
            min(len(transaction.extractionWarnings) * 0.04, 0.12),
            field="extractionWarnings",
            observed_value=transaction.extractionWarnings
        )
        
    return factors

def predict_fraud_score(transaction: Transaction, context: dict[str, Any], dt: datetime) -> float:
    if model is None or feature_cols is None:
        # Fallback score if model is not loaded
        score = 0.08
        if transaction.amount >= 5000:
            score += 0.35
        elif transaction.amount >= 1500:
            score += 0.18
        txn_type = (transaction.transactionType or "").upper()
        if txn_type in {"ATM_WITHDRAWAL", "ONLINE_PURCHASE", "FUND_TRANSFER"}:
            score += 0.12
        merchant = (transaction.merchant or "").lower()
        if any(term in merchant for term in ("crypto", "gift card", "unknown", "betting", "gambling")):
            score += 0.16
        location = (transaction.location or "").lower()
        if any(term in location for term in ("unknown", "offshore", "high risk")):
            score += 0.16
        if is_late_night(dt):
            score += 0.18
        if transaction.extractionWarnings:
            score += min(len(transaction.extractionWarnings) * 0.04, 0.12)
        return float(np.clip(score, 0.01, 0.98))

    # Preprocess request parameters into 22 features matching the model columns
    merchant_lower = (transaction.merchant or "").lower()
    location_lower = (transaction.location or "").lower()
    
    # Calculate merchant_risk_score
    if any(term in merchant_lower for term in ("crypto", "gift card", "betting", "gambling", "offshore", "forex")):
        merchant_risk_score = 0.8
    elif "unknown" in merchant_lower:
        merchant_risk_score = 0.5
    else:
        merchant_risk_score = 0.25
        
    # Calculate ip_risk_score
    if any(term in location_lower for term in ("unknown", "offshore", "high risk")):
        ip_risk_score = 0.6
    else:
        ip_risk_score = 0.15
        
    # Calculate is_international
    is_international = 1 if any(term in location_lower or term in merchant_lower for term in ("offshore", "international")) else 0
    
    # payment channels mapping
    txn_type = (transaction.transactionType or "").upper()
    payment_channel_card = "CARD" in txn_type or txn_type in ("ONLINE_PURCHASE", "ATM_WITHDRAWAL")
    payment_channel_upi = "UPI" in txn_type or txn_type in ("FUND_TRANSFER")
    payment_channel_wallet = "WALLET" in txn_type
    
    # construct all features in dictionary (numeric 0/1 for sklearn)
    features = {
        "account_age_days": context.get("account_age_days", 365),
        "credit_score_band": context.get("credit_score_band", 3),
        "kyc_level": context.get("kyc_level", 2),
        "avg_monthly_spend": context.get("avg_monthly_spend", 5000.0),
        "merchant_risk_score": merchant_risk_score,
        "transaction_amount": transaction.amount,
        "is_international": is_international,
        "ip_risk_score": ip_risk_score,
        "txn_count_1h": context.get("txn_count_1h", 1),
        "txn_count_24h": context.get("txn_count_24h", 3),
        "failed_txn_count_24h": context.get("failed_txn_count_24h", 0),
        "geo_distance_from_last_txn": context.get("geo_distance_from_last_txn", 10.0),
        "amount_deviation_from_user_mean": context.get("amount_deviation_from_user_mean", 0.0),
        "hour": dt.hour,
        "day": dt.day,
        "month": dt.month,
        "is_after_june": 1 if dt.month > 6 else 0,
        "payment_channel_card": int(payment_channel_card),
        "payment_channel_upi": int(payment_channel_upi),
        "payment_channel_wallet": int(payment_channel_wallet),
        "device_type_mobile": int(context.get("device_type_mobile", True)),
        "device_type_tablet": int(context.get("device_type_tablet", False)),
    }

    # Convert to DataFrame
    input_df = pd.DataFrame([features])
    
    # Make sure all feature columns exist and are ordered correctly
    for col in feature_cols:
        if col not in input_df.columns:
            input_df[col] = 0
            
    input_df = input_df[feature_cols]
    
    # Model predict probability
    prob = model.predict_proba(input_df)[0][1]
    return float(prob)

@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "FraudGuard ML Service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modelLoaded": str(model is not None),
        "featuresLoaded": str(feature_cols is not None)
    }

@app.post("/predict")
def predict(payload: PredictionRequest) -> dict[str, Any]:
    transaction = payload.transaction
    context = payload.context
    
    dt = parse_time(transaction.transactionTime)
    
    # Calculate ML fraud probability and explainable rule factors
    prob = predict_fraud_score(transaction, context, dt)
    factors = check_suspicious_factors(transaction, dt)
    rule_score = float(np.clip(0.08 + sum(f["weight"] for f in factors), 0.01, 0.98))
    fraud_probability = round(max(prob, rule_score), 2)
    level = risk_level(fraud_probability)
    
    # If ML model predicted high risk but rules didn't catch anything, add an ML factor
    if level in {"HIGH", "MEDIUM"} and not factors:
        add_factor(
            factors,
            "ML_ANOMALY_DETECTED",
            f"Machine learning model flagged transaction patterns as {level.lower()} risk.",
            fraud_probability
        )
        
    explanation = (
        f"{level} risk based on {len(factors)} suspicious factor(s)."
        if factors
        else "LOW risk because no major suspicious behavior was detected."
    )
    
    return {
        "fraudProbability": fraud_probability,
        "riskLevel": level,
        "explanation": explanation,
        "suspiciousFactors": factors,
        "modelVersion": "python-ml-rf-v1.0" if model is not None else "python-ml-fallback-v1.0",
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
    }
