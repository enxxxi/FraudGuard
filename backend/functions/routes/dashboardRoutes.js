const router = require("express").Router();
const { getDashboardStats } = require("../controllers/dashboardController");
const { validateQuery } = require("../middleware/validateRequest");
const { dashboardStatsQuerySchema } = require("../validators/fraudValidators");

router.get("/stats", validateQuery(dashboardStatsQuerySchema), getDashboardStats);

module.exports = router;
