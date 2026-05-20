const morgan = require("morgan");

// Small, readable HTTP logs for local emulators and deployed functions logs.
const requestLogger = morgan(":method :url :status :response-time ms");

module.exports = { requestLogger };
