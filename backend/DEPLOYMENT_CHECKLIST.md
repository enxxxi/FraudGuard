# FraudGuard Backend Deployment Checklist

## Local Verification

- Install dependencies from `backend/functions` with `npm install`.
- Confirm local Node version matches Firebase Functions target Node 20.
- Run `npm run lint`.
- Start emulators from `backend/functions` with `npm run serve`.
- Test `GET /health`.
- Test `POST /fraud/predict` with a high-risk sample transaction.
- Test `POST /email/analyze` with a simulated bank notification.
- Test `GET /fraud/analyses?userId=demo-user`.
- Test `GET /fraud/analyses/:id?userId=demo-user`.
- Test `GET /dashboard/stats?userId=demo-user`.

## Firebase Configuration

- Confirm `.firebaserc` points to the correct Firebase project.
- Deploy Firestore indexes from `backend/firestore.indexes.json`.
- Deploy Firestore rules from `backend/firestore.rules`.
- Confirm Cloud Functions environment variables are set:
  - `NODE_ENV`
  - `CORS_ORIGIN`
  - `HIGH_AMOUNT_THRESHOLD`
  - `MEDIUM_AMOUNT_THRESHOLD`
  - `FREQUENCY_WINDOW_MINUTES`
  - `FREQUENCY_COUNT_THRESHOLD`
  - `ML_SERVICE_ENABLED`
  - `ML_SERVICE_URL`

## Security Review

- Direct Firestore access must require authentication.
- Users may only read/write transaction analysis documents where `request.auth.uid == userId`.
- Backend writes should continue to happen through Firebase Admin SDK in Cloud Functions.
- Do not expose raw production emails in dashboard responses unless the frontend needs them.
- Keep delete disabled for transaction records unless an explicit retention policy is added.

## Deployment

- From `backend/functions`, run `npm run deploy` for Functions.
- From `backend`, deploy rules and indexes with Firebase CLI if not included in the deploy command.
- After deploy, run smoke tests against the production Functions URL.
- Check Firebase Functions logs for validation errors, Firestore index errors, and ML service fallback behavior.

## Future ML Service

- The Python ML service is not implemented yet.
- Keep `ML_SERVICE_ENABLED=false` until a FastAPI or Flask `/predict` service exists.
- The expected ML response should match the current rule-based analysis shape:
  - `fraudProbability`
  - `riskLevel`
  - `explanation`
  - `suspiciousFactors`
  - `modelVersion`
  - `analyzedAt`
