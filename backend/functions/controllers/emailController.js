const { asyncHandler } = require("../utils/asyncHandler");
const { AppError } = require("../utils/AppError");
const { parseBankEmail } = require("../services/emailParserService");
const { analyzeTransaction } = require("../services/fraudDetectionService");
const { saveAnalysis } = require("../services/transactionRepository");

const analyzeEmail = asyncHandler(async (req, res) => {
  const { emailContent, userId = "demo-user" } = req.body;

  if (!emailContent || typeof emailContent !== "string") {
    throw new AppError("emailContent is required and must be a string.", 400);
  }

  const extractedTransaction = parseBankEmail(emailContent);
  const analysis = await analyzeTransaction(extractedTransaction, { userId });
  const saved = await saveAnalysis({
    source: "email",
    rawEmail: emailContent,
    transaction: extractedTransaction,
    analysis,
    userId
  });

  res.status(200).json({
    transactionId: saved.id,
    extractedTransaction,
    ...analysis
  });
});

module.exports = { analyzeEmail };
