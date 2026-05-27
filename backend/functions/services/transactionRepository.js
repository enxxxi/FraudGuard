const { FieldValue, Timestamp } = require("firebase-admin/firestore");
const { db } = require("../firebase");

const TRANSACTIONS_COLLECTION = "transactions";

const saveAnalysis = async ({ source, rawEmail = null, transaction, analysis, userId }) => {
  const payload = {
    userId,
    source,
    rawEmail,
    transaction,
    analysis,
    createdAt: FieldValue.serverTimestamp(),
    updatedAt: FieldValue.serverTimestamp()
  };

  const ref = await db.collection(TRANSACTIONS_COLLECTION).add(payload);
  return { id: ref.id, ...payload };
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

  return snapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data()
  }));
};

const getTransactionsByUser = async ({ userId, limit = 200 }) => {
  const snapshot = await db
    .collection(TRANSACTIONS_COLLECTION)
    .where("userId", "==", userId)
    .orderBy("createdAt", "desc")
    .limit(limit)
    .get();

  return snapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data()
  }));
};

module.exports = {
  getRecentTransactionsByUser,
  getTransactionsByUser,
  saveAnalysis,
  TRANSACTIONS_COLLECTION
};
