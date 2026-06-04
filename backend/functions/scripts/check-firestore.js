const admin = require("firebase-admin");

process.env.FIRESTORE_EMULATOR_HOST = "localhost:8080";
process.env.GCLOUD_PROJECT = "fraudguard-wie2003";

if (!admin.apps.length) {
  admin.initializeApp();
}

const db = admin.firestore();

async function main() {
  const snapshot = await db.collection("transactions").get();
  console.log(`Found ${snapshot.size} transactions in Firestore emulator.`);
  snapshot.docs.forEach(doc => {
    const data = doc.data();
    console.log(`- ID: ${doc.id}, userId: ${data.userId}, source: ${data.source}, rawEmail: ${data.rawEmail ? data.rawEmail.substring(0, 40) + '...' : null}, amount: ${data.transaction?.amount}`);
  });
}

main().catch(console.error);
