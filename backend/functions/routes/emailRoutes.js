const router = require("express").Router();
const { analyzeEmail } = require("../controllers/emailController");
const { requireStringBodyFields } = require("../middleware/validateRequest");

router.post("/analyze", requireStringBodyFields(["emailContent"]), analyzeEmail);

module.exports = router;
