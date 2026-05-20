const { asyncHandler } = require("../utils/asyncHandler");
const { AppError } = require("../utils/AppError");
const { analyzeTransaction } = require("../services/fraudDetectionService");
const { saveAnalysis } = require("../services/transactionRepository");

const predictFraud = asyncHandler(async (req, res) => {
  const { userId = "demo-user", ...transaction } = req.body;

  if (!transaction.amount || !transaction.merchant) {
    throw new AppError("amount and merchant are required.", 400, {
      requiredFields: ["amount", "merchant"],
      example: {
        amount: 8500,
        transactionType: "ONLINE_PURCHASE",
        transactionTime: "2026-05-21T02:03:00+08:00",
        merchant: "Unknown Electronics Store",
        location: "Lagos, Nigeria"
      }
    });
  }

  const analysis = await analyzeTransaction(transaction, { userId });
  const saved = await saveAnalysis({
    source: "api",
    transaction,
    analysis,
    userId
  });

  res.status(200).json({
    transactionId: saved.id,
    ...analysis
  });
});

module.exports = { predictFraud };
