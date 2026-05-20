# FraudGuard ML Service Placeholder

This folder is reserved for the future Python ML microservice.

Planned contract:

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

Set `ML_SERVICE_ENABLED=true` and `ML_SERVICE_URL=http://127.0.0.1:8000` in `functions/.env` when the Python service is ready.
