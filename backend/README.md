# FraudGuard Backend

Production-style Firebase Functions backend for FraudGuard, an AI/ML-ready fraud detection system that analyzes simulated bank transaction email notifications in real time.

## Architecture

```text
backend/
├── firebase.json
├── functions/
│   ├── index.js
│   ├── app.js
│   ├── firebase.js
│   ├── routes/
│   ├── controllers/
│   ├── services/
│   ├── middleware/
│   ├── utils/
│   └── config/
├── ml-service/
├── .env.example
└── README.md
```

Request flow:

```text
HTTP request -> Express route -> Controller -> Service -> Firestore -> JSON response
```

## APIs

When running in the Firebase emulator, the base URL is:

```text
http://127.0.0.1:5001/<your-project-id>/us-central1/api
```

### GET /health

Health check for the backend.

Example response:

```json
{
  "status": "ok",
  "service": "FraudGuard Backend",
  "environment": "development",
  "timestamp": "2026-05-21T02:03:00.000Z"
}
```

### POST /api/email/analyze

Parses simulated bank email content, extracts transaction fields, scores fraud risk, stores the analysis, and returns the result.

Postman payload:

```json
{
  "userId": "demo-user",
  "emailContent": "Alert: RM8,500.00 was spent at Unknown Crypto Exchange on 2026-05-21 02:03. Location: Unknown. If this was not you, contact support."
}
```

Example response:

```json
{
  "transactionId": "abc123",
  "extractedTransaction": {
    "amount": 8500,
    "transactionType": "PURCHASE",
    "transactionTime": "2026-05-21T02:03:00.000Z",
    "merchant": "Unknown Crypto Exchange",
    "location": "Unknown",
    "currency": "MYR"
  },
  "fraudProbability": 0.93,
  "riskLevel": "HIGH",
  "explanation": "HIGH risk because amount 8500 exceeds high threshold 5000, transaction occurred between midnight and 5 am, merchant name matches a suspicious or unusual merchant pattern, location is unknown or has been marked as high risk.",
  "suspiciousFactors": [
    {
      "code": "UNUSUALLY_HIGH_AMOUNT",
      "reason": "Amount 8500 exceeds high threshold 5000.",
      "weight": 0.35
    }
  ],
  "modelVersion": "rules-mvp-v1",
  "analyzedAt": "2026-05-21T02:03:00.000Z"
}
```

### POST /api/fraud/predict

Accepts transaction JSON directly and returns fraud analysis.

Postman payload:

```json
{
  "userId": "demo-user",
  "amount": 2250,
  "transactionType": "TRANSFER",
  "transactionTime": "2026-05-21T23:20:00+08:00",
  "merchant": "Maybank Transfer",
  "location": "Kuala Lumpur, Malaysia"
}
```

Example response:

```json
{
  "transactionId": "def456",
  "fraudProbability": 0.26,
  "riskLevel": "LOW",
  "explanation": "LOW risk because amount 2250 exceeds medium threshold 1500.",
  "suspiciousFactors": [
    {
      "code": "ELEVATED_AMOUNT",
      "reason": "Amount 2250 exceeds medium threshold 1500.",
      "weight": 0.18
    }
  ],
  "modelVersion": "rules-mvp-v1",
  "analyzedAt": "2026-05-21T02:03:00.000Z"
}
```

### GET /api/dashboard/stats

Returns analytics data for dashboard cards and charts.

Example:

```text
GET /api/dashboard/stats?userId=demo-user
```

Example response:

```json
{
  "totalTransactions": 12,
  "fraudCount": 3,
  "highRiskCount": 3,
  "fraudTrendData": [
    {
      "date": "2026-05-21",
      "total": 12,
      "fraud": 3,
      "highRisk": 3
    }
  ],
  "generatedAt": "2026-05-21T02:03:00.000Z"
}
```

## MVP Fraud Logic

The backend currently uses rule-based scoring so the project is hackathon-ready before ML integration.

Rules:

- unusually high amount
- late-night transaction
- abnormal transaction frequency
- unusual merchant
- suspicious location

Risk levels:

- `LOW`: probability below `0.40`
- `MEDIUM`: probability from `0.40` to `0.69`
- `HIGH`: probability `0.70` and above

## Firestore Schema Suggestions

### transactions

```json
{
  "userId": "demo-user",
  "source": "email",
  "rawEmail": "Alert: RM8,500...",
  "transaction": {
    "amount": 8500,
    "currency": "MYR",
    "transactionType": "PURCHASE",
    "transactionTime": "2026-05-21T02:03:00.000Z",
    "merchant": "Unknown Crypto Exchange",
    "location": "Unknown"
  },
  "analysis": {
    "fraudProbability": 0.93,
    "riskLevel": "HIGH",
    "explanation": "HIGH risk because...",
    "suspiciousFactors": [],
    "modelVersion": "rules-mvp-v1",
    "analyzedAt": "2026-05-21T02:03:00.000Z"
  },
  "createdAt": "serverTimestamp",
  "updatedAt": "serverTimestamp"
}
```

Recommended indexes:

- `transactions`: `userId ASC`, `createdAt DESC`
- `transactions`: `userId ASC`, `createdAt DESC`, `analysis.riskLevel ASC` if you later query by risk level

### users

```json
{
  "email": "student@example.com",
  "displayName": "Demo User",
  "role": "analyst",
  "createdAt": "serverTimestamp"
}
```

### alerts

```json
{
  "transactionId": "abc123",
  "userId": "demo-user",
  "riskLevel": "HIGH",
  "status": "OPEN",
  "createdAt": "serverTimestamp"
}
```

## Setup

Install Firebase CLI if needed:

```powershell
npm install -g firebase-tools
```

Install Functions dependencies:

```powershell
cd backend/functions
npm install
```

Create local environment file:

```powershell
Copy-Item ..\.env.example .\.env
```

Create a Firebase project config:

```powershell
cd ..
Copy-Item .\.firebaserc.example .\.firebaserc
```

Edit `.firebaserc` and replace `your-firebase-project-id`.

## Run Locally With Emulators

From `backend/functions`:

```powershell
npm run serve
```

Or from `backend`:

```powershell
firebase emulators:start --only functions,firestore,auth
```

Emulator UI:

```text
http://127.0.0.1:4000
```

## Deploy

Login and select your Firebase project:

```powershell
firebase login
firebase use <your-firebase-project-id>
```

Deploy functions:

```powershell
cd backend/functions
npm run deploy
```

## Python ML Service Integration

The Node backend is ready for a Python ML microservice through `functions/services/mlClientService.js`.

Expected future Python endpoint:

```text
POST http://127.0.0.1:8000/predict
```

Enable it by setting:

```text
ML_SERVICE_ENABLED=true
ML_SERVICE_URL=http://127.0.0.1:8000
```

Until then, FraudGuard uses the local rule-based MVP engine.
