const { getTransactionsByUser } = require("./transactionRepository");

const toDayKey = (value) => {
  const date = value?.toDate ? value.toDate() : new Date(value || Date.now());
  return date.toISOString().slice(0, 10);
};

const incrementMapCount = (map, key) => {
  const normalizedKey = key || "UNKNOWN";
  map.set(normalizedKey, (map.get(normalizedKey) || 0) + 1);
};

const toCountItems = (map, keyName) => Array.from(map.entries())
  .map(([key, count]) => ({ [keyName]: key, count }))
  .sort((a, b) => b.count - a.count || String(a[keyName]).localeCompare(String(b[keyName])));

const toTransactionTypeItems = (map) => Array.from(map.entries())
  .map(([transactionType, summary]) => ({
    transactionType,
    count: summary.count,
    averageFraudProbability: summary.count
      ? Number((summary.totalFraudProbability / summary.count).toFixed(2))
      : 0
  }))
  .sort((a, b) => b.count - a.count || a.transactionType.localeCompare(b.transactionType));

const getDashboardStats = async ({ userId }) => {
  const transactions = await getTransactionsByUser({ userId });

  const totalTransactions = transactions.length;
  const fraudCount = transactions.filter((item) => item.analysis?.fraudProbability >= 0.7).length;
  const highRiskCount = transactions.filter((item) => item.analysis?.riskLevel === "HIGH").length;
  const blockedExposure = transactions
    .filter((item) => item.analysis?.riskLevel === "HIGH")
    .reduce((sum, item) => sum + Number(item.transaction?.amount || 0), 0);
  const totalFraudProbability = transactions.reduce(
    (sum, item) => sum + Number(item.analysis?.fraudProbability || 0),
    0
  );

  const trendMap = transactions.reduce((acc, item) => {
    const day = toDayKey(item.createdAt);
    const current = acc.get(day) || { date: day, total: 0, fraud: 0, highRisk: 0 };

    current.total += 1;
    if (item.analysis?.fraudProbability >= 0.7) current.fraud += 1;
    if (item.analysis?.riskLevel === "HIGH") current.highRisk += 1;

    acc.set(day, current);
    return acc;
  }, new Map());

  const riskDistributionMap = new Map();
  const transactionTypeMap = new Map();
  const sourceMap = new Map();

  transactions.forEach((item) => {
    const transactionType = item.transaction?.transactionType || "UNKNOWN";
    const typeSummary = transactionTypeMap.get(transactionType) || {
      count: 0,
      totalFraudProbability: 0
    };

    typeSummary.count += 1;
    typeSummary.totalFraudProbability += Number(item.analysis?.fraudProbability || 0);

    incrementMapCount(riskDistributionMap, item.analysis?.riskLevel);
    transactionTypeMap.set(transactionType, typeSummary);
    incrementMapCount(sourceMap, item.source);
  });

  return {
    totalTransactions,
    fraudCount,
    highRiskCount,
    mediumRiskCount: transactions.filter((item) => item.analysis?.riskLevel === "MEDIUM").length,
    lowRiskCount: transactions.filter((item) => item.analysis?.riskLevel === "LOW").length,
    averageFraudProbability: totalTransactions
      ? Number((totalFraudProbability / totalTransactions).toFixed(2))
      : 0,
    blockedExposure: Number(blockedExposure.toFixed(2)),
    fraudTrendData: Array.from(trendMap.values()).sort((a, b) => a.date.localeCompare(b.date)),
    riskDistribution: toCountItems(riskDistributionMap, "riskLevel"),
    transactionTypeBreakdown: toTransactionTypeItems(transactionTypeMap),
    sourceBreakdown: toCountItems(sourceMap, "source"),
    recentHighRiskAnalyses: transactions
      .filter((item) => item.analysis?.riskLevel === "HIGH")
      .slice(0, 5)
      .map((item) => ({
        id: item.id,
        source: item.source,
        amount: item.transaction?.amount,
        currency: item.transaction?.currency,
        merchant: item.transaction?.merchant,
        riskLevel: item.analysis?.riskLevel,
        fraudProbability: item.analysis?.fraudProbability,
        createdAt: item.createdAt
      })),
    generatedAt: new Date().toISOString()
  };
};

module.exports = { getDashboardStats };
