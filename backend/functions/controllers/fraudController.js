const { asyncHandler } = require("../utils/asyncHandler");
const { AppError } = require("../utils/AppError");
const { sendSuccess } = require("../utils/apiResponse");
const { analyzeTransaction } = require("../services/fraudDetectionService");
const {
  getSavedAnalysisById,
  listSavedAnalysesByUser,
  saveAnalysis
} = require("../services/transactionRepository");

const predictFraud = asyncHandler(async (req, res) => {
  const { userId = "demo-user", ...transaction } = req.body;

  const analysis = await analyzeTransaction(transaction, { userId });
  const saved = await saveAnalysis({
    source: "api",
    transaction,
    analysis,
    userId
  });

  sendSuccess(res, {
    transactionId: saved.id,
    ...analysis
  });
});

const listSavedAnalyses = asyncHandler(async (req, res) => {
  const {
    userId = "demo-user",
    limit,
    riskLevel = null,
    source = null
  } = req.query;

  const analyses = await listSavedAnalysesByUser({
    userId,
    limit,
    riskLevel,
    source
  });

  sendSuccess(res, { analyses }, 200, { count: analyses.length });
});

const getSavedAnalysis = asyncHandler(async (req, res) => {
  const { id } = req.params;
  const { userId = "demo-user" } = req.query;

  const savedAnalysis = await getSavedAnalysisById({ id, userId });

  if (!savedAnalysis) {
    throw new AppError("Saved transaction analysis was not found.", 404, { id });
  }

  sendSuccess(res, savedAnalysis);
});

module.exports = {
  getSavedAnalysis,
  listSavedAnalyses,
  predictFraud
};
