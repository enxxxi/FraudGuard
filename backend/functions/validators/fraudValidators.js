const { z } = require("zod");
const {
  ANALYSIS_SOURCES,
  RISK_LEVELS,
  TRANSACTION_DIRECTIONS,
  TRANSACTION_TYPES
} = require("../schemas/transactionAnalysisSchema");

const userIdSchema = z.string().trim().min(1).max(128).default("demo-user");

const fraudPredictionBodySchema = z.object({
  userId: userIdSchema.optional(),
  amount: z.coerce.number().positive(),
  currency: z.string().trim().min(3).max(12).optional(),
  transactionType: z.enum(TRANSACTION_TYPES).optional(),
  direction: z.enum(TRANSACTION_DIRECTIONS).optional(),
  transactionTime: z.string().trim().min(1).optional(),
  merchant: z.string().trim().min(1).max(160),
  location: z.string().trim().min(1).max(160).optional(),
  referenceId: z.string().trim().min(1).max(80).nullable().optional(),
  extractionWarnings: z.array(z.string().trim().min(1).max(300)).max(20).optional()
});

const savedAnalysesQuerySchema = z.object({
  userId: userIdSchema,
  limit: z.coerce.number().int().positive().max(500).optional(),
  riskLevel: z.enum(RISK_LEVELS).optional(),
  source: z.enum(ANALYSIS_SOURCES).optional()
});

const savedAnalysisByIdQuerySchema = z.object({
  userId: userIdSchema
});

const dashboardStatsQuerySchema = z.object({
  userId: userIdSchema
});

module.exports = {
  dashboardStatsQuerySchema,
  fraudPredictionBodySchema,
  savedAnalysesQuerySchema,
  savedAnalysisByIdQuerySchema
};
