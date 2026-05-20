const { getTransactionsByUser } = require("./transactionRepository");

const toDayKey = (value) => {
  const date = value?.toDate ? value.toDate() : new Date(value || Date.now());
  return date.toISOString().slice(0, 10);
};

const getDashboardStats = async ({ userId }) => {
  const transactions = await getTransactionsByUser({ userId });

  const totalTransactions = transactions.length;
  const fraudCount = transactions.filter((item) => item.analysis?.fraudProbability >= 0.7).length;
  const highRiskCount = transactions.filter((item) => item.analysis?.riskLevel === "HIGH").length;

  const trendMap = transactions.reduce((acc, item) => {
    const day = toDayKey(item.createdAt);
    const current = acc.get(day) || { date: day, total: 0, fraud: 0, highRisk: 0 };

    current.total += 1;
    if (item.analysis?.fraudProbability >= 0.7) current.fraud += 1;
    if (item.analysis?.riskLevel === "HIGH") current.highRisk += 1;

    acc.set(day, current);
    return acc;
  }, new Map());

  return {
    totalTransactions,
    fraudCount,
    highRiskCount,
    fraudTrendData: Array.from(trendMap.values()).sort((a, b) => a.date.localeCompare(b.date)),
    generatedAt: new Date().toISOString()
  };
};

module.exports = { getDashboardStats };
