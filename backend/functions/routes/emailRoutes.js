const router = require("express").Router();
const { analyzeEmail } = require("../controllers/emailController");
const { validateBody } = require("../middleware/validateRequest");
const { emailAnalyzeBodySchema } = require("../validators/emailValidators");

router.post("/analyze", validateBody(emailAnalyzeBodySchema), analyzeEmail);

module.exports = router;
