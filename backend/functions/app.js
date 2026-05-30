require("dotenv").config();

const cors = require("cors");
const express = require("express");
const helmet = require("helmet");

const { env } = require("./config/env");
const apiRoutes = require("./routes");
const { requestLogger } = require("./middleware/requestLogger");
const { notFoundHandler } = require("./middleware/notFoundHandler");
const { errorHandler } = require("./middleware/errorHandler");
const { sendSuccess } = require("./utils/apiResponse");

const app = express();

app.use(helmet());
app.use(cors({ origin: env.corsOrigin, credentials: true }));
app.use(express.json({ limit: "1mb" }));
app.use(express.urlencoded({ extended: true }));
app.use(requestLogger);

app.get("/health", (req, res) => {
  sendSuccess(res, {
    status: "ok",
    service: "FraudGuard Backend",
    environment: env.nodeEnv,
    timestamp: new Date().toISOString()
  });
});

// The Firebase Function is already exported as "api", so these routes should
// mount at the Express root. Emulator URL:
// /<project-id>/us-central1/api/email/analyze
app.use("/", apiRoutes);
app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
