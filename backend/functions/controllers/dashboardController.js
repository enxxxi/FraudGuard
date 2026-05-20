const { asyncHandler } = require("../utils/asyncHandler");
const { getDashboardStats: fetchDashboardStats } = require("../services/dashboardService");

const getDashboardStats = asyncHandler(async (req, res) => {
  const { userId = "demo-user" } = req.query;
  const stats = await fetchDashboardStats({ userId });
  res.status(200).json(stats);
});

module.exports = { getDashboardStats };
