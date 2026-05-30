const { asyncHandler } = require("../utils/asyncHandler");
const { sendSuccess } = require("../utils/apiResponse");
const { getDashboardStats: fetchDashboardStats } = require("../services/dashboardService");

const getDashboardStats = asyncHandler(async (req, res) => {
  const { userId = "demo-user" } = req.query;
  const stats = await fetchDashboardStats({ userId });
  sendSuccess(res, stats);
});

module.exports = { getDashboardStats };
