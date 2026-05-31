const router = require("express").Router();
const {
  getSavedAnalysis,
  listSavedAnalyses,
  predictFraud
} = require("../controllers/fraudController");
const { validateBody, validateQuery } = require("../middleware/validateRequest");
const {
  fraudPredictionBodySchema,
  savedAnalysesQuerySchema,
  savedAnalysisByIdQuerySchema
} = require("../validators/fraudValidators");

router.post("/predict", validateBody(fraudPredictionBodySchema), predictFraud);
router.get("/analyses", validateQuery(savedAnalysesQuerySchema), listSavedAnalyses);
router.get("/analyses/:id", validateQuery(savedAnalysisByIdQuerySchema), getSavedAnalysis);

module.exports = router;
