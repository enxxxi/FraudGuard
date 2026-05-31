const { z } = require("zod");

const emailAnalyzeBodySchema = z.object({
  userId: z.string().trim().min(1).max(128).default("demo-user").optional(),
  emailContent: z.string().trim().min(1).max(20000)
});

module.exports = { emailAnalyzeBodySchema };
