"""Seed demo transactions into the local or Firebase-backed API."""

from __future__ import annotations

import json
import os
import sys
from urllib import request

API_BASE_URL = os.getenv("FRAUDGUARD_API_BASE_URL", "http://127.0.0.1:8787").rstrip("/")
USER_ID = os.getenv("FRAUDGUARD_USER_ID", "demo-user")

SAMPLES = [
    "Alert: RM8,500.00 was spent at Unknown Crypto Exchange on 2026-05-21 02:03. Location: Unknown.",
    "Maybank2u: RM245.90 card purchase at Tesco Extra on 2026-05-20 14:22. Location: Kuala Lumpur.",
    "Fund transfer of RM1,750.00 to Maybank Transfer on 2026-05-21 23:20. Location: Kuala Lumpur.",
    "ATM withdrawal RM600.00 at 2026-05-19 03:15 from unknown location.",
    "RM120.00 online purchase at Shopee on 2026-05-18 11:05. Location: Petaling Jaya.",
]


def post_email(email_content: str) -> None:
    payload = json.dumps({"userId": USER_ID, "emailContent": email_content}).encode("utf-8")
    req = request.Request(
        f"{API_BASE_URL}/email/analyze",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=15) as response:
        body = json.loads(response.read().decode("utf-8"))
        data = body.get("data", body)
        print(
            f"  -> {data.get('riskLevel')} ({int(float(data.get('fraudProbability', 0)) * 100)}%) "
            f"txn={data.get('transactionId')}"
        )


def main() -> int:
    print(f"Seeding {len(SAMPLES)} analyses to {API_BASE_URL} for user {USER_ID}")
    for sample in SAMPLES:
        try:
            post_email(sample)
        except Exception as exc:
            print(f"Failed: {exc}", file=sys.stderr)
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
