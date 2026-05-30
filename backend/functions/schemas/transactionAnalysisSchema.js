const { AppError } = require("../utils/AppError");

const SAVED_ANALYSIS_SCHEMA_VERSION = 1;

const ANALYSIS_SOURCES = ["api", "email"];
const TRANSACTION_TYPES = [
  "ATM_WITHDRAWAL",
  "ONLINE_PURCHASE",
  "FUND_TRANSFER",
  "CARD_PURCHASE",
  "BILL_PAYMENT",
  "ACCOUNT_CREDIT",
  "UNKNOWN"
];
const TRANSACTION_DIRECTIONS = ["DEBIT", "CREDIT", "UNKNOWN"];
const RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"];

const DEFAULT_TRANSACTION = {
  currency: "MYR",
  transactionType: "UNKNOWN",
  direction: "UNKNOWN",
  merchant: "Unknown Merchant",
  location: "Unknown",
  referenceId: null,
  extractionWarnings: []
};

const stripUndefined = (value) => {
  if (Array.isArray(value)) {
    return value.map(stripUndefined);
  }

  if (value && typeof value === "object") {
    return Object.entries(value).reduce((acc, [key, entry]) => {
      if (entry !== undefined) {
        acc[key] = stripUndefined(entry);
      }

      return acc;
    }, {});
  }

  return value;
};

const normalizeString = (value, fallback = null, maxLength = 500) => {
  if (value === null || value === undefined) return fallback;

  const normalized = String(value).trim();
  if (!normalized) return fallback;

  return normalized.slice(0, maxLength);
};

const normalizeEnum = (value, allowedValues, fallback) => {
  const normalized = normalizeString(value, fallback);
  return allowedValues.includes(normalized) ? normalized : fallback;
};

const normalizeIsoDate = (value, fallback = null) => {
  const date = value ? new Date(value) : null;

  if (!date || Number.isNaN(date.getTime())) {
    return fallback;
  }

  return date.toISOString();
};

const normalizeNumber = (value, fieldName, { min = null, max = null, required = false } = {}) => {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    if (required) {
      throw new AppError(`${fieldName} must be a valid number.`, 400, { field: fieldName });
    }

    return null;
  }

  if (min !== null && numberValue < min) {
    throw new AppError(`${fieldName} must be at least ${min}.`, 400, { field: fieldName, min });
  }

  if (max !== null && numberValue > max) {
    throw new AppError(`${fieldName} must be at most ${max}.`, 400, { field: fieldName, max });
  }

  return numberValue;
};

const normalizeWarnings = (warnings) => {
  if (!Array.isArray(warnings)) return [];

  return warnings
    .map((warning) => normalizeString(warning, null, 300))
    .filter(Boolean)
    .slice(0, 20);
};

const normalizeSuspiciousFactors = (factors) => {
  if (!Array.isArray(factors)) return [];

  return factors.slice(0, 25).map((factor) => stripUndefined({
    code: normalizeString(factor?.code, "UNKNOWN_FACTOR", 80),
    reason: normalizeString(factor?.reason, "No reason provided.", 500),
    weight: normalizeNumber(factor?.weight, "suspiciousFactors.weight", { min: 0, max: 1 }) ?? 0,
    field: normalizeString(factor?.field, null, 80),
    observedValue: factor?.observedValue ?? null
  }));
};

const inferRiskLevel = (fraudProbability) => {
  if (fraudProbability >= 0.7) return "HIGH";
  if (fraudProbability >= 0.4) return "MEDIUM";
  return "LOW";
};

const normalizeTransaction = (transaction = {}) => {
  const amount = normalizeNumber(transaction.amount, "transaction.amount", {
    min: 0.01,
    required: true
  });

  return stripUndefined({
    amount,
    currency: normalizeString(transaction.currency, DEFAULT_TRANSACTION.currency, 12).toUpperCase(),
    transactionType: normalizeEnum(
      transaction.transactionType,
      TRANSACTION_TYPES,
      DEFAULT_TRANSACTION.transactionType
    ),
    direction: normalizeEnum(transaction.direction, TRANSACTION_DIRECTIONS, DEFAULT_TRANSACTION.direction),
    transactionTime: normalizeIsoDate(transaction.transactionTime, new Date().toISOString()),
    merchant: normalizeString(transaction.merchant, DEFAULT_TRANSACTION.merchant, 160),
    location: normalizeString(transaction.location, DEFAULT_TRANSACTION.location, 160),
    referenceId: normalizeString(transaction.referenceId, DEFAULT_TRANSACTION.referenceId, 80),
    extractionWarnings: normalizeWarnings(transaction.extractionWarnings)
  });
};

const normalizeAnalysis = (analysis = {}) => {
  const fraudProbability = normalizeNumber(analysis.fraudProbability, "analysis.fraudProbability", {
    min: 0,
    max: 1,
    required: true
  });

  return stripUndefined({
    fraudProbability,
    riskLevel: normalizeEnum(analysis.riskLevel, RISK_LEVELS, inferRiskLevel(fraudProbability)),
    explanation: normalizeString(analysis.explanation, "No explanation provided.", 1200),
    suspiciousFactors: normalizeSuspiciousFactors(analysis.suspiciousFactors),
    scoringSummary: stripUndefined(analysis.scoringSummary || {}),
    modelVersion: normalizeString(analysis.modelVersion, "unknown", 80),
    analyzedAt: normalizeIsoDate(analysis.analyzedAt, new Date().toISOString())
  });
};

const buildSavedAnalysisData = ({ source, rawEmail = null, transaction, analysis, userId }) => {
  const normalizedUserId = normalizeString(userId, null, 128);

  if (!normalizedUserId) {
    throw new AppError("userId is required to save a transaction analysis.", 400, { field: "userId" });
  }

  return stripUndefined({
    schemaVersion: SAVED_ANALYSIS_SCHEMA_VERSION,
    userId: normalizedUserId,
    source: normalizeEnum(source, ANALYSIS_SOURCES, "api"),
    rawEmail: rawEmail === null ? null : normalizeString(rawEmail, null, 20000),
    transaction: normalizeTransaction(transaction),
    analysis: normalizeAnalysis(analysis)
  });
};

module.exports = {
  ANALYSIS_SOURCES,
  RISK_LEVELS,
  SAVED_ANALYSIS_SCHEMA_VERSION,
  TRANSACTION_DIRECTIONS,
  TRANSACTION_TYPES,
  buildSavedAnalysisData,
  normalizeAnalysis,
  normalizeTransaction,
  stripUndefined
};
