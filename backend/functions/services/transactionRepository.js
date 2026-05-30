const { FieldValue, Timestamp } = require("firebase-admin/firestore");
const { db } = require("../firebase");
const {
  ANALYSIS_SOURCES,
  buildSavedAnalysisData,
  RISK_LEVELS
} = require("../schemas/transactionAnalysisSchema");
const { AppError } = require("../utils/AppError");

const TRANSACTIONS_COLLECTION = "transactions";
const DEFAULT_PAGE_SIZE = 200;
const MAX_PAGE_SIZE = 500;

const clampLimit = (limit = DEFAULT_PAGE_SIZE) => {
  const parsedLimit = Number(limit);

  if (!Number.isInteger(parsedLimit) || parsedLimit <= 0) {
    return DEFAULT_PAGE_SIZE;
  }

  return Math.min(parsedLimit, MAX_PAGE_SIZE);
};

const serializeSavedAnalysis = (doc) => {
  const data = doc.data();

  return {
    id: doc.id,
    ...data,
    createdAt: data.createdAt?.toDate ? data.createdAt.toDate().toISOString() : data.createdAt,
    updatedAt: data.updatedAt?.toDate ? data.updatedAt.toDate().toISOString() : data.updatedAt
  };
};

const createSavedAnalysis = async ({ source, rawEmail = null, transaction, analysis, userId }) => {
  const payload = {
    ...buildSavedAnalysisData({ source, rawEmail, transaction, analysis, userId }),
    createdAt: FieldValue.serverTimestamp(),
    updatedAt: FieldValue.serverTimestamp()
  };

  const ref = await db.collection(TRANSACTIONS_COLLECTION).add(payload);
  const savedDoc = await ref.get();
  return serializeSavedAnalysis(savedDoc);
};

const saveAnalysis = createSavedAnalysis;

const getSavedAnalysisById = async ({ id, userId = null }) => {
  if (!id) {
    throw new AppError("Transaction analysis id is required.", 400, { field: "id" });
  }

  const doc = await db.collection(TRANSACTIONS_COLLECTION).doc(id).get();

  if (!doc.exists) {
    return null;
  }

  const savedAnalysis = serializeSavedAnalysis(doc);

  if (userId && savedAnalysis.userId !== userId) {
    return null;
  }

  return savedAnalysis;
};

const getRecentTransactionsByUser = async ({ userId, minutes }) => {
  const since = new Date(Date.now() - minutes * 60 * 1000);

  const snapshot = await db
    .collection(TRANSACTIONS_COLLECTION)
    .where("userId", "==", userId)
    .where("createdAt", ">=", Timestamp.fromDate(since))
    .orderBy("createdAt", "desc")
    .limit(25)
    .get();

  return snapshot.docs.map(serializeSavedAnalysis);
};

const listSavedAnalysesByUser = async ({ userId, limit = DEFAULT_PAGE_SIZE, riskLevel = null, source = null }) => {
  if (!userId) {
    throw new AppError("userId is required to list transaction analyses.", 400, { field: "userId" });
  }

  let query = db.collection(TRANSACTIONS_COLLECTION).where("userId", "==", userId);

  if (riskLevel) {
    if (!RISK_LEVELS.includes(riskLevel)) {
      throw new AppError("riskLevel filter is invalid.", 400, { field: "riskLevel", allowedValues: RISK_LEVELS });
    }

    query = query.where("analysis.riskLevel", "==", riskLevel);
  }

  if (source) {
    if (!ANALYSIS_SOURCES.includes(source)) {
      throw new AppError("source filter is invalid.", 400, { field: "source", allowedValues: ANALYSIS_SOURCES });
    }

    query = query.where("source", "==", source);
  }

  const snapshot = await query
    .orderBy("createdAt", "desc")
    .limit(clampLimit(limit))
    .get();

  return snapshot.docs.map(serializeSavedAnalysis);
};

const getTransactionsByUser = listSavedAnalysesByUser;

module.exports = {
  createSavedAnalysis,
  getSavedAnalysisById,
  getRecentTransactionsByUser,
  getTransactionsByUser,
  listSavedAnalysesByUser,
  saveAnalysis,
  TRANSACTIONS_COLLECTION
};
