const { env } = require("../config/env");

const predictWithMlService = async (transaction, context = {}) => {
  const response = await fetch(`${env.mlServiceUrl}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      transaction,
      context
    })
  });

  if (!response.ok) {
    throw new Error(`ML service failed with status ${response.status}`);
  }

  return response.json();
};

module.exports = { predictWithMlService };
