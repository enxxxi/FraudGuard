const { auth } = require("../firebase");
const { AppError } = require("../utils/AppError");

// Optional middleware for endpoints that should require Firebase Auth later.
const requireAuth = async (req, res, next) => {
  try {
    const header = req.headers.authorization || "";
    const token = header.startsWith("Bearer ") ? header.slice(7) : null;

    if (!token) {
      throw new AppError("Missing Firebase Auth bearer token.", 401);
    }

    req.user = await auth.verifyIdToken(token);
    return next();
  } catch (error) {
    return next(error.statusCode ? error : new AppError("Invalid or expired auth token.", 401));
  }
};

module.exports = { requireAuth };
