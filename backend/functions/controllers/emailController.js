const { asyncHandler } = require("../utils/asyncHandler");
const { sendSuccess } = require("../utils/apiResponse");
const { parseBankEmail } = require("../services/emailParserService");
const { analyzeTransaction } = require("../services/fraudDetectionService");
const { saveAnalysis } = require("../services/transactionRepository");

const analyzeEmail = asyncHandler(async (req, res) => {
  const { emailContent, userId = "demo-user" } = req.body;

  const extractedTransaction = parseBankEmail(emailContent);
  const analysis = await analyzeTransaction(extractedTransaction, { userId });
  const saved = await saveAnalysis({
    source: "email",
    rawEmail: emailContent,
    transaction: extractedTransaction,
    analysis,
    userId
  });

  sendSuccess(res, {
    transactionId: saved.id,
    extractedTransaction,
    ...analysis
  });
});

module.exports = { analyzeEmail };
