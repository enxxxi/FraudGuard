const sendSuccess = (res, data, statusCode = 200, meta = null) => {
  res.status(statusCode).json({
    success: true,
    data,
    meta: meta || undefined
  });
};

module.exports = { sendSuccess };
