const { AppError } = require("../utils/AppError");

const requireBodyFields = (fields) => (req, _res, next) => {
  const missingFields = fields.filter((field) => {
    const value = req.body?.[field];
    return value === undefined || value === null || value === "";
  });

  if (missingFields.length) {
    return next(new AppError("Required request fields are missing.", 400, {
      missingFields,
      requiredFields: fields
    }));
  }

  return next();
};

const requireStringBodyFields = (fields) => (req, _res, next) => {
  const invalidFields = fields.filter((field) => {
    const value = req.body?.[field];
    return typeof value !== "string" || !value.trim();
  });

  if (invalidFields.length) {
    return next(new AppError("Required request fields must be non-empty strings.", 400, {
      invalidFields,
      requiredFields: fields
    }));
  }

  return next();
};

module.exports = {
  requireBodyFields,
  requireStringBodyFields
};
