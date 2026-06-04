"""
Lightweight local FraudGuard API for development without Firebase CLI.

Mirrors the Node/Firebase Functions contract used by the Streamlit dashboard.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8000").rstrip("/")

app = FastAPI(title="FraudGuard Local API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_DATA_DIR = Path(__file__).resolve().parent / "data"
_STORE_FILE = Path(os.getenv("FRAUDGUARD_LOCAL_STORE_PATH", str(_DATA_DIR / "demo_analyses.json")))
_store: list[dict[str, Any]] = []


def _load_store_from_disk() -> None:
    if not _STORE_FILE.exists():
        return
    try:
        with _STORE_FILE.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, list):
            _store[:] = loaded
    except (OSError, json.JSONDecodeError):
        pass


def _persist_store_to_disk() -> None:
    try:
        _STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _STORE_FILE.open("w", encoding="utf-8") as handle:
            json.dump(_store, handle, indent=2)
    except OSError:
        pass


_load_store_from_disk()


class EmailAnalyzeBody(BaseModel):
    userId: str = "demo-user"
    emailContent: str = Field(min_length=1)


class FraudPredictBody(BaseModel):
    userId: str = "demo-user"
    amount: float = Field(gt=0)
    currency: str | None = "MYR"
    transactionType: str | None = "CARD_PURCHASE"
    direction: str | None = "DEBIT"
    transactionTime: str | None = None
    merchant: str = "Unknown Merchant"
    location: str | None = "Unknown"
    referenceId: str | None = None
    extractionWarnings: list[str] = Field(default_factory=list)
    transactionId: str | None = None
    deviceType: str | None = "MOBILE"


def _success(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"success": True, "data": data}
    if meta:
        payload["meta"] = meta
    return payload


def _parse_email(email_content: str) -> dict[str, Any]:
    amount_match = re.search(r"(?:RM|MYR|\$)\s*([\d,]+(?:\.\d{2})?)", email_content, re.I)
    amount = float(amount_match.group(1).replace(",", "")) if amount_match else 100.0

    merchant = "Unknown Merchant"
    merchant_match = re.search(r"(?:at|from|to)\s+([^.\n]+)", email_content, re.I)
    if merchant_match:
        merchant = merchant_match.group(1).strip()[:160]

    location = "Unknown"
    # Pattern 1: location/country followed by colon/dash
    loc_match1 = re.search(r"\b(?:location|country)\s*[:\-]\s*([A-Za-z\s\.-]{2,50})", email_content, re.I)
    if loc_match1:
        val = loc_match1.group(1).strip()
        if val.lower() != "unknown" and val:
            location = val[:160]
    else:
        # Pattern 2: location/country in/of/at [Location]
        loc_match2 = re.search(r"\b(?:location|country)\s+(?:in|of|at)\s+([A-Za-z\s\.-]{2,50})", email_content, re.I)
        if loc_match2:
            val = loc_match2.group(1).strip()
            if val.lower() != "unknown" and val:
                location = val[:160]
        else:
            # Pattern 3: recipient in/at [Location]
            loc_match3 = re.search(r"\brecipient\s+(?:in|at)\s+([A-Za-z\s\.-]{2,50})", email_content, re.I)
            if loc_match3:
                val = loc_match3.group(1).strip()
                if val.lower() != "unknown" and val:
                    location = val[:160]

    txn_type = "CARD_PURCHASE"
    lowered = email_content.lower()
    if "transfer" in lowered or "fund" in lowered:
        txn_type = "FUND_TRANSFER"
    elif "atm" in lowered or "withdraw" in lowered:
        txn_type = "ATM_WITHDRAWAL"
    elif "online" in lowered:
        txn_type = "ONLINE_PURCHASE"

    # Extract Date: e.g. YYYY-MM-DD
    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", email_content)
    date_str = date_match.group(1) if date_match else None

    # Extract Time: e.g. at 03:41 AM, at 03:41, 03:41 AM
    time_str = None
    time_patterns = [
        r"\b(?:at|time)\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?)\b",
        r"\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b",
        r"\b(\d{1,2}:\d{2})\b"
    ]
    for pat in time_patterns:
        t_match = re.search(pat, email_content, re.I)
        if t_match:
            time_str = t_match.group(1).strip()
            break

    # Try standard YYYY-MM-DD[ T]HH:MM first
    dt_match = re.search(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})", email_content)
    if dt_match:
        try:
            transaction_time = datetime.fromisoformat(dt_match.group(1).replace(" ", "T")).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            transaction_time = datetime.now(timezone.utc).isoformat()
    elif date_str or time_str:
        if date_str:
            try:
                dt_part = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                dt_part = datetime.now(timezone.utc)
        else:
            dt_part = datetime.now(timezone.utc)

        hour, minute = 12, 0
        if time_str:
            t_clean = time_str.lower()
            is_pm = "pm" in t_clean
            is_am = "am" in t_clean
            t_digits = re.search(r"(\d{1,2}):(\d{2})", t_clean)
            if t_digits:
                hour = int(t_digits.group(1))
                minute = int(t_digits.group(2))
                if is_pm and hour < 12:
                    hour += 12
                elif is_am and hour == 12:
                    hour = 0
        else:
            now = datetime.now(timezone.utc)
            hour, minute = now.hour, now.minute

        final_dt = dt_part.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc)
        transaction_time = final_dt.isoformat()
    else:
        transaction_time = datetime.now(timezone.utc).isoformat()

    warnings: list[str] = []
    if location == "Unknown":
        warnings.append("Location could not be confidently detected.")

    return {
        "amount": amount,
        "currency": "MYR",
        "transactionType": txn_type,
        "direction": "DEBIT",
        "transactionTime": transaction_time,
        "merchant": merchant,
        "location": location,
        "referenceId": None,
        "extractionWarnings": warnings,
    }


async def _predict(transaction: dict[str, Any], user_id: str, device_type: str | None = "MOBILE") -> dict[str, Any]:
    dt_mobile = 1 if (device_type or "MOBILE").upper() == "MOBILE" else 0
    dt_tablet = 1 if (device_type or "MOBILE").upper() == "TABLET" else 0
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/predict",
            json={
                "transaction": transaction,
                "context": {
                    "userId": user_id,
                    "device_type_mobile": dt_mobile,
                    "device_type_tablet": dt_tablet,
                }
            },
        )

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"ML service error: {response.text}")

    return response.json()


def _save_record(
    *,
    user_id: str,
    source: str,
    transaction: dict[str, Any],
    analysis: dict[str, Any],
    raw_email: str | None = None,
    custom_id: str | None = None,
) -> dict[str, Any]:
    record = {
        "id": custom_id or str(uuid.uuid4()),
        "userId": user_id,
        "source": source,
        "rawEmail": raw_email,
        "transaction": transaction,
        "analysis": analysis,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    _store.insert(0, record)
    _persist_store_to_disk()
    return record


def _dashboard_stats(user_id: str) -> dict[str, Any]:
    items = [item for item in _store if item["userId"] == user_id]
    total = len(items)
    fraud_count = sum(1 for item in items if item["analysis"].get("fraudProbability", 0) >= 0.7)
    high_risk = sum(1 for item in items if item["analysis"].get("riskLevel") == "HIGH")
    avg_prob = (
        sum(item["analysis"].get("fraudProbability", 0) for item in items) / total if total else 0
    )
    blocked = sum(
        item["transaction"].get("amount", 0)
        for item in items
        if item["analysis"].get("riskLevel") == "HIGH"
    )

    trend_map: dict[str, dict[str, Any]] = {}
    for item in items:
        day = item["createdAt"][:10]
        bucket = trend_map.setdefault(day, {"date": day, "total": 0, "fraud": 0, "highRisk": 0})
        bucket["total"] += 1
        if item["analysis"].get("fraudProbability", 0) >= 0.7:
            bucket["fraud"] += 1
        if item["analysis"].get("riskLevel") == "HIGH":
            bucket["highRisk"] += 1

    return {
        "totalTransactions": total,
        "fraudCount": fraud_count,
        "highRiskCount": high_risk,
        "mediumRiskCount": sum(1 for item in items if item["analysis"].get("riskLevel") == "MEDIUM"),
        "lowRiskCount": sum(1 for item in items if item["analysis"].get("riskLevel") == "LOW"),
        "averageFraudProbability": round(avg_prob, 2),
        "blockedExposure": round(blocked, 2),
        "fraudTrendData": sorted(trend_map.values(), key=lambda row: row["date"]),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    return _success(
        {
            "status": "ok",
            "service": "FraudGuard Local API",
            "mlServiceUrl": ML_SERVICE_URL,
            "storedAnalyses": len(_store),
            "persistedTo": str(_STORE_FILE),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.post("/email/analyze")
async def analyze_email(body: EmailAnalyzeBody) -> dict[str, Any]:
    transaction = _parse_email(body.emailContent)
    analysis = await _predict(transaction, body.userId)
    saved = _save_record(
        user_id=body.userId,
        source="email",
        transaction=transaction,
        analysis=analysis,
        raw_email=body.emailContent,
    )
    return _success(
        {
            "transactionId": saved["id"],
            "extractedTransaction": transaction,
            **analysis,
        }
    )


@app.post("/fraud/predict")
async def predict_fraud(body: FraudPredictBody) -> dict[str, Any]:
    transaction = body.model_dump(exclude={"userId", "transactionId", "deviceType"})
    analysis = await _predict(transaction, body.userId, device_type=body.deviceType)
    saved = _save_record(
        user_id=body.userId,
        source="api",
        transaction=transaction,
        analysis=analysis,
        custom_id=body.transactionId,
    )
    return _success({"transactionId": saved["id"], **analysis})


@app.get("/fraud/analyses")
async def list_analyses(
    userId: str = Query(default="demo-user"),
    limit: int = Query(default=200, ge=1, le=500),
) -> dict[str, Any]:
    items = [item for item in _store if item["userId"] == userId][:limit]
    return _success({"analyses": items}, meta={"count": len(items)})


@app.get("/dashboard/stats")
async def dashboard_stats(userId: str = Query(default="demo-user")) -> dict[str, Any]:
    return _success(_dashboard_stats(userId))
