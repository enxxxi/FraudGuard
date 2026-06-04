const fs = require("fs");
const path = require("path");
const admin = require("firebase-admin");

process.env.FIRESTORE_EMULATOR_HOST = "localhost:8080";
process.env.GCLOUD_PROJECT = "fraudguard-wie2003";

if (!admin.apps.length) {
  admin.initializeApp();
}
const db = admin.firestore();

const JSON_STORE_PATH = path.resolve(__dirname, "../../local-api/data/demo_analyses.json");

const samplePatterns = [
  /RM8,500\.00.*spent at Unknown Crypto Exchange/i,
  /RM245\.90.*purchase at Tesco Extra/i,
  /RM1,750\.00.*to Maybank Transfer/i,
  /ATM withdrawal RM600\.00/i,
  /RM120\.00.*purchase at Shopee/i
];

function isHardcoded(record) {
  if (!record.rawEmail) return false;
  return samplePatterns.some(pattern => pattern.test(record.rawEmail));
}

async function main() {
  console.log("Starting database synchronization and cleanup...");

  // 1. Read local JSON store
  let localStore = [];
  if (fs.existsSync(JSON_STORE_PATH)) {
    try {
      const content = fs.readFileSync(JSON_STORE_PATH, "utf8");
      localStore = JSON.parse(content);
      console.log(`Read ${localStore.length} records from local JSON store.`);
    } catch (err) {
      console.error("Failed to read local JSON store:", err);
    }
  } else {
    console.log("Local JSON store does not exist. Creating a new one.");
  }

  // 2. Filter local store (remove hardcoded, keep user-tried)
  const userTriedLocal = localStore.filter(record => !isHardcoded(record));
  console.log(`- Filtered local store: kept ${userTriedLocal.length} user-tried records, deleted ${localStore.length - userTriedLocal.length} hardcoded records.`);

  // 3. Query Firestore emulator
  console.log("Querying Firestore emulator...");
  const snapshot = await db.collection("transactions").get();
  console.log(`Read ${snapshot.size} documents from Firestore.`);

  const firestoreDocs = [];
  const docsToDelete = [];

  snapshot.docs.forEach(doc => {
    const data = doc.data();
    // Convert timestamps to string ISO representation for matching
    const record = {
      id: doc.id,
      ...data,
      createdAt: data.createdAt?.toDate ? data.createdAt.toDate().toISOString() : data.createdAt,
      updatedAt: data.updatedAt?.toDate ? data.updatedAt.toDate().toISOString() : data.updatedAt
    };

    if (isHardcoded(record)) {
      docsToDelete.push(doc.id);
    } else {
      firestoreDocs.push(record);
    }
  });

  console.log(`- Identified ${docsToDelete.length} hardcoded Firestore documents to delete.`);
  console.log(`- Identified ${firestoreDocs.length} user-tried Firestore documents.`);

  // 4. Delete hardcoded documents from Firestore
  for (const docId of docsToDelete) {
    await db.collection("transactions").doc(docId).delete();
    console.log(`  Deleted hardcoded Firestore doc: ${docId}`);
  }

  // 5. Merge user-tried records from both databases
  const mergedMap = new Map();
  // Add local user-tried first
  userTriedLocal.forEach(r => mergedMap.set(r.id, r));
  // Add firestore user-tried (overwriting/updating if IDs match)
  firestoreDocs.forEach(r => mergedMap.set(r.id, r));

  const mergedStore = Array.from(mergedMap.values());
  console.log(`Merged database contains ${mergedStore.length} unique user-tried records.`);

  // 6. Write missing user-tried records to Firestore
  for (const item of mergedStore) {
    const docRef = db.collection("transactions").doc(item.id);
    const docSnapshot = await docRef.get();

    if (!docSnapshot.exists) {
      console.log(`  Writing user-tried record ${item.id} to Firestore...`);
      await docRef.set({
        schemaVersion: item.schemaVersion || 1,
        userId: item.userId || "demo-user",
        source: item.source || "email",
        rawEmail: item.rawEmail || null,
        transaction: item.transaction,
        analysis: item.analysis,
        createdAt: admin.firestore.Timestamp.fromDate(new Date(item.createdAt)),
        updatedAt: admin.firestore.Timestamp.fromDate(new Date(item.updatedAt))
      });
    }
  }

  // 7. Sort merged store by createdAt desc and save to JSON
  mergedStore.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  fs.mkdirSync(path.dirname(JSON_STORE_PATH), { recursive: true });
  fs.writeFileSync(JSON_STORE_PATH, JSON.stringify(mergedStore, null, 2), "utf8");
  console.log(`Saved ${mergedStore.length} synchronized records to ${JSON_STORE_PATH}.`);

  console.log("Database synchronization and cleanup complete!");
}

main()
  .then(() => process.exit(0))
  .catch(err => {
    console.error("Execution failed:", err);
    process.exit(1);
  });
