require("dotenv").config();

const cors = require("cors");
const express = require("express");
const helmet = require("helmet");

const { env } = require("./config/env");
const apiRoutes = require("./routes");
const { requestLogger } = require("./middleware/requestLogger");
const { notFoundHandler } = require("./middleware/notFoundHandler");
const { errorHandler } = require("./middleware/errorHandler");

const app = express();

app.use(helmet());
app.use(cors({ origin: env.corsOrigin, credentials: true }));
app.use(express.json({ limit: "1mb" }));
app.use(express.urlencoded({ extended: true }));
app.use(requestLogger);

app.get("/health", (req, res) => {
  res.status(200).json({
    status: "ok",
    service: "FraudGuard Backend",
    environment: env.nodeEnv,
    timestamp: new Date().toISOString()
  });
});

app.use("/api", apiRoutes);
app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
