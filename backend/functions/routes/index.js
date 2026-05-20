const router = require("express").Router();

const dashboardRoutes = require("./dashboardRoutes");
const emailRoutes = require("./emailRoutes");
const fraudRoutes = require("./fraudRoutes");

router.use("/email", emailRoutes);
router.use("/fraud", fraudRoutes);
router.use("/dashboard", dashboardRoutes);

module.exports = router;
