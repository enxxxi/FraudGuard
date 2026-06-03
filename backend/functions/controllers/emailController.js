const { asyncHandler } = require("../utils/asyncHandler");
const { sendSuccess } = require("../utils/apiResponse");
const { parseBankEmail } = require("../services/emailParserService");
const { analyzeTransaction } = require("../services/fraudDetectionService");
const { saveAnalysis } = require("../services/transactionRepository");

const analyzeEmail = asyncHandler(async (req, res) => {
  const {
    userId = "demo-user",
    emailContent,
    sender,
    subject,
    body
  } = req.body;
  const email = emailContent
    ? { sender, subject, body: emailContent }
    : { sender, subject, body };

  const extraction = parseBankEmail(email);
  const analysis = await analyzeTransaction(extraction.fraudTransaction, { userId });
  const saved = extraction.fraudTransaction.amount === null
    ? null
    : await saveAnalysis({
      source: "email",
      rawEmail: email.body,
      transaction: extraction.fraudTransaction,
      analysis,
      userId
    });

  sendSuccess(res, {
    transactionId: saved?.id || null,
    parsedTransaction: extraction.parsedTransaction,
    extractionMetadata: extraction.metadata,
    fraudAnalysisInput: extraction.fraudTransaction,
    ...analysis
  });
});

module.exports = { analyzeEmail };
