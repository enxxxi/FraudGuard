# FraudGuard ML Service

FastAPI microservice for the optional Python fraud predictor. The current
implementation mirrors the MVP rules engine contract so the Node backend can
switch to it with `ML_SERVICE_ENABLED=true`.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Then set these in `backend/functions/.env`:

```env
ML_SERVICE_ENABLED=true
ML_SERVICE_URL=http://127.0.0.1:8000
```

## Contract

```http
POST /predict
Content-Type: application/json
```

```json
{
  "transaction": {
    "amount": 8500,
    "transactionType": "ONLINE_PURCHASE",
    "transactionTime": "2026-05-21T02:03:00+08:00",
    "merchant": "Unknown Crypto Exchange",
    "location": "Unknown"
  },
  "context": {
    "userId": "demo-user"
  }
}
```

Expected response:

```json
{
  "fraudProbability": 0.92,
  "riskLevel": "HIGH",
  "explanation": "High risk based on model features.",
  "suspiciousFactors": [
    {
      "code": "MODEL_HIGH_RISK",
      "reason": "Model classified this transaction as high risk.",
      "weight": 0.92
    }
  ],
  "modelVersion": "python-ml-v1",
  "analyzedAt": "2026-05-21T02:03:00.000Z"
}
```

Health check:

```http
GET /health
```
