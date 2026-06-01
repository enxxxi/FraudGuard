from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="FraudGuard ML Service", version="0.1.0")


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


def clamp(value: float, minimum: float = 0.01, maximum: float = 0.98) -> float:
    return max(minimum, min(maximum, value))


def is_late_night(transaction_time: str | None) -> bool:
    if not transaction_time:
        return False

    try:
        parsed = datetime.fromisoformat(transaction_time.replace("Z", "+00:00"))
    except ValueError:
        return False

    return 0 <= parsed.hour < 5


def add_factor(factors: list[dict[str, Any]], code: str, reason: str, weight: float) -> float:
    factors.append({
        "code": code,
        "reason": reason,
        "weight": weight,
    })
    return weight


def risk_level(probability: float) -> str:
    if probability >= 0.7:
        return "HIGH"
    if probability >= 0.4:
        return "MEDIUM"
    return "LOW"


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "FraudGuard ML Service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/predict")
def predict(payload: PredictionRequest) -> dict[str, Any]:
    transaction = payload.transaction
    factors: list[dict[str, Any]] = []
    score = 0.08

    if transaction.amount >= 5000:
        score += add_factor(
            factors,
            "UNUSUALLY_HIGH_AMOUNT",
            "Transaction amount is above the high-risk threshold.",
            0.35,
        )
    elif transaction.amount >= 1000:
        score += add_factor(
            factors,
            "ELEVATED_AMOUNT",
            "Transaction amount is above the medium-risk threshold.",
            0.18,
        )

    if (transaction.transactionType or "").upper() in {"ATM_WITHDRAWAL", "ONLINE_PURCHASE", "FUND_TRANSFER"}:
        score += add_factor(
            factors,
            "RISKY_TRANSACTION_TYPE",
            "Transaction type has elevated fraud exposure.",
            0.12,
        )

    merchant = (transaction.merchant or "").lower()
    if any(term in merchant for term in ("crypto", "gift card", "unknown", "betting", "gambling")):
        score += add_factor(
            factors,
            "UNUSUAL_MERCHANT",
            "Merchant matches a suspicious pattern.",
            0.16,
        )

    location = (transaction.location or "").lower()
    if any(term in location for term in ("unknown", "offshore", "high risk")):
        score += add_factor(
            factors,
            "SUSPICIOUS_LOCATION",
            "Location is unknown or marked as high risk.",
            0.16,
        )

    if is_late_night(transaction.transactionTime):
        score += add_factor(
            factors,
            "LATE_NIGHT_TRANSACTION",
            "Transaction occurred between midnight and 5 AM.",
            0.18,
        )

    if transaction.extractionWarnings:
        score += add_factor(
            factors,
            "LOW_EXTRACTION_CONFIDENCE",
            "Email parsing produced extraction warnings.",
            min(len(transaction.extractionWarnings) * 0.04, 0.12),
        )

    fraud_probability = round(clamp(score), 2)
    level = risk_level(fraud_probability)
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
        "modelVersion": "python-ml-rules-v0.1",
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
    }
