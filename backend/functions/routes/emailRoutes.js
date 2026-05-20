const router = require("express").Router();
const { analyzeEmail } = require("../controllers/emailController");

router.post("/analyze", analyzeEmail);

module.exports = router;
