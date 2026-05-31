const { ZodError } = require("zod");
const { AppError } = require("../utils/AppError");

const formatZodIssues = (error) => error.issues.map((issue) => ({
  field: issue.path.join(".") || "request",
  message: issue.message
}));

const validate = (schema, source) => (req, _res, next) => {
  const result = schema.safeParse(req[source]);

  if (!result.success) {
    const details = formatZodIssues(result.error);
    return next(new AppError(`Invalid ${source}.`, 400, { validationErrors: details }));
  }

  req[source] = result.data;
  return next();
};

const validateBody = (schema) => validate(schema, "body");

const validateQuery = (schema) => validate(schema, "query");

const isValidationError = (error) => error instanceof ZodError;

module.exports = {
  isValidationError,
  validateBody,
  validateQuery
};
