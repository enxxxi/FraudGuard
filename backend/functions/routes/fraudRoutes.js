const router = require("express").Router();
const {
  getSavedAnalysis,
  listSavedAnalyses,
  predictFraud
} = require("../controllers/fraudController");
const { requireBodyFields } = require("../middleware/validateRequest");

router.post("/predict", requireBodyFields(["amount", "merchant"]), predictFraud);
router.get("/analyses", listSavedAnalyses);
router.get("/analyses/:id", getSavedAnalysis);

module.exports = router;
