const toNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const parseCorsOrigin = (value) => {
  if (!value || value === "*") {
    return true;
  }

  return value.split(",").map((origin) => origin.trim()).filter(Boolean);
};

const env = {
  nodeEnv: process.env.NODE_ENV || "development",
  logLevel: process.env.LOG_LEVEL || "info",
  firebaseProjectId: process.env.FIREBASE_PROJECT_ID || process.env.GCLOUD_PROJECT,
  corsOrigin: parseCorsOrigin(process.env.CORS_ORIGIN),
  highAmountThreshold: toNumber(process.env.HIGH_AMOUNT_THRESHOLD, 5000),
  mediumAmountThreshold: toNumber(process.env.MEDIUM_AMOUNT_THRESHOLD, 1500),
  frequencyWindowMinutes: toNumber(process.env.FREQUENCY_WINDOW_MINUTES, 10),
  frequencyCountThreshold: toNumber(process.env.FREQUENCY_COUNT_THRESHOLD, 3),
  mlServiceUrl: process.env.ML_SERVICE_URL || "http://127.0.0.1:8000",
  mlServiceEnabled: process.env.ML_SERVICE_ENABLED === "true"
};

module.exports = { env };
