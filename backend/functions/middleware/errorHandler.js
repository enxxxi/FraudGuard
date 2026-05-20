const { env } = require("../config/env");

const errorHandler = (err, req, res, next) => {
  const statusCode = err.statusCode || 500;

  console.error("Request failed", {
    method: req.method,
    path: req.originalUrl,
    statusCode,
    message: err.message,
    details: err.details
  });

  res.status(statusCode).json({
    error: {
      message: statusCode === 500 ? "Internal server error" : err.message,
      details: err.details || undefined,
      requestId: req.headers["x-cloud-trace-context"] || undefined,
      stack: env.nodeEnv === "development" ? err.stack : undefined
    }
  });
};

module.exports = { errorHandler };
