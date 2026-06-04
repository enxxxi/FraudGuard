/**
 * sync-to-production.js
 * Reads local demo_analyses.json and uploads all records to production Firestore.
 * Usage: node scripts/sync-to-production.js
 *
 * Requires: GOOGLE_APPLICATION_CREDENTIALS env var pointing to a service account key,
 *           OR being authenticated via `gcloud auth application-default login`.
 */
const fs = require("fs");
const path = require("path");
const admin = require("firebase-admin");

// Do NOT set FIRESTORE_EMULATOR_HOST — we want production Firestore
delete process.env.FIRESTORE_EMULATOR_HOST;

const PROJECT_ID = "fraudguard-wie2003";
const SERVICE_ACCOUNT_PATH = path.resolve(__dirname, "sa-key.json");

if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert(SERVICE_ACCOUNT_PATH),
    projectId: PROJECT_ID,
  });
}
const db = admin.firestore();

const JSON_STORE_PATH = path.resolve(__dirname, "../../local-api/data/demo_analyses.json");
const COLLECTION = "transactions";

async function main() {
  // 1. Read local JSON store
  if (!fs.existsSync(JSON_STORE_PATH)) {
    console.error(`Local data file not found: ${JSON_STORE_PATH}`);
    process.exit(1);
  }

  const content = fs.readFileSync(JSON_STORE_PATH, "utf8");
  const records = JSON.parse(content);
  console.log(`Read ${records.length} records from local JSON store.`);

  // 2. Check what already exists in production
  const existingSnapshot = await db.collection(COLLECTION).get();
  const existingIds = new Set(existingSnapshot.docs.map(doc => doc.id));
  console.log(`Found ${existingIds.size} existing documents in production Firestore.`);

  // 3. Upload records that don't already exist
  let uploaded = 0;
  let skipped = 0;

  for (const item of records) {
    if (existingIds.has(item.id)) {
      console.log(`  Skipping existing: ${item.id}`);
      skipped++;
      continue;
    }

    const docData = {
      schemaVersion: item.schemaVersion || 1,
      userId: item.userId || "demo-user",
      source: item.source || "email",
      rawEmail: item.rawEmail || null,
      transaction: item.transaction,
      analysis: item.analysis,
      createdAt: admin.firestore.Timestamp.fromDate(new Date(item.createdAt)),
      updatedAt: admin.firestore.Timestamp.fromDate(new Date(item.updatedAt)),
    };

    await db.collection(COLLECTION).doc(item.id).set(docData);
    console.log(`  Uploaded: ${item.id}`);
    uploaded++;
  }

  console.log(`\nSync complete!`);
  console.log(`  Uploaded: ${uploaded}`);
  console.log(`  Skipped (already exists): ${skipped}`);
  console.log(`  Total in production: ${existingIds.size + uploaded}`);
}

main()
  .then(() => process.exit(0))
  .catch(err => {
    console.error("Sync failed:", err);
    process.exit(1);
  });
