const { env } = require("../config/env");
const { getRecentTransactionsByUser } = require("./transactionRepository");
const { predictWithMlService } = require("./mlClientService");

const SUSPICIOUS_MERCHANT_PATTERNS = [
  /crypto/i,
  /gift card/i,
  /unknown/i,
  /betting/i,
  /gambling/i,
  /offshore/i
];

const SUSPICIOUS_LOCATIONS = [
  /unknown/i,
  /nigeria/i,
  /russia/i,
  /offshore/i,
  /high risk/i
];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const getRiskLevel = (probability) => {
  if (probability >= 0.7) return "HIGH";
  if (probability >= 0.4) return "MEDIUM";
  return "LOW";
};

const isLateNight = (transactionTime) => {
  const date = transactionTime ? new Date(transactionTime) : new Date();
  const hour = date.getHours();
  return hour >= 0 && hour < 5;
};

const buildExplanation = (riskLevel, suspiciousFactors) => {
  if (!suspiciousFactors.length) {
    return "No major suspicious behavior was detected. The transaction matches normal MVP rule thresholds.";
  }

  const reasons = suspiciousFactors.map((factor) => factor.reason.replace(/\.$/, "").toLowerCase());
  return `${riskLevel} risk because ${reasons.join(", ")}.`;
};

const scoreWithRules = async (transaction, context = {}) => {
  const suspiciousFactors = [];
  let score = 0.08;

  const amount = Number(transaction.amount);
  if (amount >= env.highAmountThreshold) {
    score += 0.35;
    suspiciousFactors.push({
      code: "UNUSUALLY_HIGH_AMOUNT",
      reason: `Amount ${amount} exceeds high threshold ${env.highAmountThreshold}.`,
      weight: 0.35
    });
  } else if (amount >= env.mediumAmountThreshold) {
    score += 0.18;
    suspiciousFactors.push({
      code: "ELEVATED_AMOUNT",
      reason: `Amount ${amount} exceeds medium threshold ${env.mediumAmountThreshold}.`,
      weight: 0.18
    });
  }

  if (isLateNight(transaction.transactionTime)) {
    score += 0.18;
    suspiciousFactors.push({
      code: "LATE_NIGHT_TRANSACTION",
      reason: "Transaction occurred between midnight and 5 AM.",
      weight: 0.18
    });
  }

  if (SUSPICIOUS_MERCHANT_PATTERNS.some((pattern) => pattern.test(transaction.merchant || ""))) {
    score += 0.16;
    suspiciousFactors.push({
      code: "UNUSUAL_MERCHANT",
      reason: "Merchant name matches a suspicious or unusual merchant pattern.",
      weight: 0.16
    });
  }

  if (SUSPICIOUS_LOCATIONS.some((pattern) => pattern.test(transaction.location || ""))) {
    score += 0.16;
    suspiciousFactors.push({
      code: "SUSPICIOUS_LOCATION",
      reason: "Location is unknown or has been marked as high risk.",
      weight: 0.16
    });
  }

  if (context.userId) {
    const recentTransactions = await getRecentTransactionsByUser({
      userId: context.userId,
      minutes: env.frequencyWindowMinutes
    });

    if (recentTransactions.length >= env.frequencyCountThreshold) {
      score += 0.17;
      suspiciousFactors.push({
        code: "ABNORMAL_FREQUENCY",
        reason: `${recentTransactions.length} recent transactions found in ${env.frequencyWindowMinutes} minutes.`,
        weight: 0.17
      });
    }
  }

  const fraudProbability = Number(clamp(score, 0.01, 0.98).toFixed(2));
  const riskLevel = getRiskLevel(fraudProbability);

  return {
    fraudProbability,
    riskLevel,
    explanation: buildExplanation(riskLevel, suspiciousFactors),
    suspiciousFactors,
    modelVersion: "rules-mvp-v1",
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
