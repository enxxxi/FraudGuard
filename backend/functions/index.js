const functions = require("firebase-functions");
const app = require("./app");

// Firebase Functions export style.
// Local emulator URL:
// http://127.0.0.1:5001/<project-id>/us-central1/api
exports.api = functions.https.onRequest(app);
