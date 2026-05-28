const { env } = require("../config/env");
const { getRecentTransactionsByUser } = require("./transactionRepository");
const { predictWithMlService } = require("./mlClientService");

const LOCAL_CURRENCY = "MYR";
const LOCAL_TIME_ZONE = "Asia/Kuala_Lumpur";

const SUSPICIOUS_MERCHANT_PATTERNS = [
  /crypto/i,
  /gift card/i,
  /unknown/i,
  /betting/i,
  /gambling/i,
  /offshore/i,
  /forex/i
];

const SUSPICIOUS_LOCATIONS = [
  /unknown/i,
  /nigeria/i,
  /russia/i,
  /offshore/i,
  /high risk/i
];

const TRANSACTION_TYPE_RISK_WEIGHTS = {
  ATM_WITHDRAWAL: 0.14,
  ONLINE_PURCHASE: 0.12,
  FUND_TRANSFER: 0.1,
  CARD_PURCHASE: 0.07,
  BILL_PAYMENT: 0.03,
  ACCOUNT_CREDIT: 0
};

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const getRiskLevel = (probability) => {
  if (probability >= 0.7) return "HIGH";
  if (probability >= 0.4) return "MEDIUM";
  return "LOW";
};

const isDebit = (transaction) => transaction.direction === "DEBIT";

const isCredit = (transaction) => transaction.direction === "CREDIT";

const isLateNight = (transactionTime) => {
  const date = transactionTime ? new Date(transactionTime) : new Date();

  if (Number.isNaN(date.getTime())) {
    return false;
  }

  const hourFormatter = new globalThis.Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    hourCycle: "h23",
    timeZone: LOCAL_TIME_ZONE
  });
  const hour = Number(hourFormatter.format(date));

  return hour >= 0 && hour < 5;
};

const addFactor = (factors, { code, reason, weight, field = null, observedValue = null }) => {
  factors.push({
    code,
    reason,
    weight,
    field,
    observedValue
  });

  return weight;
};

const buildExplanation = (riskLevel, suspiciousFactors) => {
  if (!suspiciousFactors.length) {
    return "No major suspicious behavior was detected. The transaction matches normal MVP rule thresholds.";
  }

  const reasons = suspiciousFactors.map((factor) => factor.reason.replace(/\.$/, "").toLowerCase());
  return `${riskLevel} risk because ${reasons.join(", ")}.`;
};

const getBaseScore = (transaction) => {
  if (isCredit(transaction)) return 0.04;
  if (isDebit(transaction)) return 0.08;
  return 0.1;
};

const applyAmountRules = ({ transaction, suspiciousFactors }) => {
  const amount = Number(transaction.amount);
  let score = 0;

  if (!Number.isFinite(amount)) {
    return addFactor(suspiciousFactors, {
      code: "INVALID_AMOUNT",
      reason: "Transaction amount is missing or invalid.",
      weight: 0.2,
      field: "amount",
      observedValue: transaction.amount
    });
  }

  if (amount >= env.highAmountThreshold) {
    score += addFactor(suspiciousFactors, {
      code: "UNUSUALLY_HIGH_AMOUNT",
      reason: `Amount ${amount} exceeds high threshold ${env.highAmountThreshold}.`,
      weight: isCredit(transaction) ? 0.16 : 0.35,
      field: "amount",
      observedValue: amount
    });
  } else if (amount >= env.mediumAmountThreshold) {
    score += addFactor(suspiciousFactors, {
      code: "ELEVATED_AMOUNT",
      reason: `Amount ${amount} exceeds medium threshold ${env.mediumAmountThreshold}.`,
      weight: isCredit(transaction) ? 0.08 : 0.18,
      field: "amount",
      observedValue: amount
    });
  }

  return score;
};

const applyTransactionTypeRules = ({ transaction, suspiciousFactors }) => {
  const transactionType = transaction.transactionType || "UNKNOWN";
  const weight = TRANSACTION_TYPE_RISK_WEIGHTS[transactionType] || 0;

  if (weight <= 0) {
    return 0;
  }

  return addFactor(suspiciousFactors, {
    code: "RISKY_TRANSACTION_TYPE",
    reason: `${transactionType} has higher fraud exposure than routine account activity.`,
    weight,
    field: "transactionType",
    observedValue: transactionType
  });
};

const applyContextRules = ({ transaction, suspiciousFactors }) => {
  let score = 0;

  if (transaction.currency && transaction.currency !== LOCAL_CURRENCY) {
    score += addFactor(suspiciousFactors, {
      code: "NON_LOCAL_CURRENCY",
      reason: `Transaction currency ${transaction.currency} differs from local currency ${LOCAL_CURRENCY}.`,
      weight: 0.1,
      field: "currency",
      observedValue: transaction.currency
    });
  }

  if (transaction.direction === "UNKNOWN") {
    score += addFactor(suspiciousFactors, {
      code: "UNKNOWN_DIRECTION",
      reason: "Transaction direction could not be classified as debit or credit.",
      weight: 0.07,
      field: "direction",
      observedValue: transaction.direction
    });
  }

  if (transaction.transactionType === "ACCOUNT_CREDIT" && isDebit(transaction)) {
    score += addFactor(suspiciousFactors, {
      code: "CONFLICTING_TRANSACTION_FIELDS",
      reason: "Transaction type suggests a credit, but direction was classified as debit.",
      weight: 0.12,
      field: "direction",
      observedValue: transaction.direction
    });
  }

  if (transaction.transactionType !== "ACCOUNT_CREDIT" && isCredit(transaction)) {
    score += addFactor(suspiciousFactors, {
      code: "CONFLICTING_TRANSACTION_FIELDS",
      reason: "Transaction direction suggests a credit, but type is not account credit.",
      weight: 0.1,
      field: "transactionType",
      observedValue: transaction.transactionType
    });
  }

  return score;
};

const applyTimeRules = ({ transaction, suspiciousFactors }) => {
  if (!isLateNight(transaction.transactionTime)) {
    return 0;
  }

  return addFactor(suspiciousFactors, {
    code: "LATE_NIGHT_TRANSACTION",
    reason: "Transaction occurred between midnight and 5 AM.",
    weight: isCredit(transaction) ? 0.08 : 0.18,
    field: "transactionTime",
    observedValue: transaction.transactionTime
  });
};

const applyMerchantRules = ({ transaction, suspiciousFactors }) => {
  const merchant = transaction.merchant || "";

  if (!SUSPICIOUS_MERCHANT_PATTERNS.some((pattern) => pattern.test(merchant))) {
    return 0;
  }

  return addFactor(suspiciousFactors, {
    code: "UNUSUAL_MERCHANT",
    reason: "Merchant name matches a suspicious or unusual merchant pattern.",
    weight: 0.16,
    field: "merchant",
    observedValue: merchant || "Unknown Merchant"
  });
};

const applyLocationRules = ({ transaction, suspiciousFactors }) => {
  const location = transaction.location || "";

  if (!SUSPICIOUS_LOCATIONS.some((pattern) => pattern.test(location))) {
    return 0;
  }

  return addFactor(suspiciousFactors, {
    code: "SUSPICIOUS_LOCATION",
    reason: "Location is unknown or has been marked as high risk.",
    weight: 0.16,
    field: "location",
    observedValue: location || "Unknown"
  });
};

const applyExtractionQualityRules = ({ transaction, suspiciousFactors }) => {
  const warnings = Array.isArray(transaction.extractionWarnings) ? transaction.extractionWarnings : [];

  if (!warnings.length) {
    return 0;
  }

  return addFactor(suspiciousFactors, {
    code: "LOW_EXTRACTION_CONFIDENCE",
    reason: `${warnings.length} extraction warning(s) were produced while parsing the email.`,
    weight: Math.min(warnings.length * 0.04, 0.12),
    field: "extractionWarnings",
    observedValue: warnings
  });
};

const applyReferenceRules = ({ transaction, suspiciousFactors }) => {
  if (transaction.referenceId || isCredit(transaction)) {
    return 0;
  }

  return addFactor(suspiciousFactors, {
    code: "MISSING_REFERENCE_ID",
    reason: "No transaction reference ID was extracted from the notification.",
    weight: 0.03,
    field: "referenceId",
    observedValue: null
  });
};

const applyFrequencyRules = async ({ transaction, context, suspiciousFactors }) => {
  if (!context.userId || isCredit(transaction)) {
    return 0;
  }

  const recentTransactions = await getRecentTransactionsByUser({
    userId: context.userId,
    minutes: env.frequencyWindowMinutes
  });

  if (recentTransactions.length < env.frequencyCountThreshold) {
    return 0;
  }

  return addFactor(suspiciousFactors, {
    code: "ABNORMAL_FREQUENCY",
    reason: `${recentTransactions.length} recent transactions found in ${env.frequencyWindowMinutes} minutes.`,
    weight: 0.17,
    field: "userId",
    observedValue: context.userId
  });
};

const scoreWithRules = async (transaction, context = {}) => {
  const suspiciousFactors = [];
  let score = getBaseScore(transaction);

  score += applyAmountRules({ transaction, suspiciousFactors });
  score += applyTransactionTypeRules({ transaction, suspiciousFactors });
  score += applyContextRules({ transaction, suspiciousFactors });
  score += applyTimeRules({ transaction, suspiciousFactors });
  score += applyMerchantRules({ transaction, suspiciousFactors });
  score += applyLocationRules({ transaction, suspiciousFactors });
  score += applyExtractionQualityRules({ transaction, suspiciousFactors });
  score += applyReferenceRules({ transaction, suspiciousFactors });
  score += await applyFrequencyRules({ transaction, context, suspiciousFactors });

  const fraudProbability = Number(clamp(score, 0.01, 0.98).toFixed(2));
  const riskLevel = getRiskLevel(fraudProbability);

  return {
    fraudProbability,
    riskLevel,
    explanation: buildExplanation(riskLevel, suspiciousFactors),
    suspiciousFactors,
    scoringSummary: {
      baseScore: getBaseScore(transaction),
      totalFactorWeight: Number((fraudProbability - getBaseScore(transaction)).toFixed(2)),
      riskThresholds: {
        lowBelow: 0.4,
        highFrom: 0.7
      }
    },
    modelVersion: "rules-mvp-v2",
    analyzedAt: new Date().toISOString()
  };
};

const analyzeTransaction = async (transaction, context = {}) => {
  if (env.mlServiceEnabled) {
    return predictWithMlService(transaction, context);
  }

  return scoreWithRules(transaction, context);
};

module.exports = {
  analyzeTransaction,
  scoreWithRules
};
