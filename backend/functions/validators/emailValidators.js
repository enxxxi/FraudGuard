const { z } = require("zod");

const emailAnalyzeBodySchema = z.object({
  userId: z.string().trim().min(1).max(128).default("demo-user").optional(),
  sender: z.string().trim().min(1).max(320).optional(),
  subject: z.string().trim().min(1).max(300).optional(),
  body: z.string().trim().min(1).max(20000).optional(),
  emailContent: z.string().trim().min(1).max(20000).optional()
}).refine((value) => value.body || value.emailContent, {
  message: "Either body or emailContent is required.",
  path: ["body"]
});

module.exports = { emailAnalyzeBodySchema };
