const { AppError } = require("../utils/AppError");

const TYPE_KEYWORDS = [
  { pattern: /withdraw|atm/i, value: "ATM_WITHDRAWAL" },
  { pattern: /transfer|sent|debited|credited/i, value: "TRANSFER" },
  { pattern: /purchase|pos|spent|paid/i, value: "PURCHASE" },
  { pattern: /bill|utility|payment/i, value: "BILL_PAYMENT" }
];

const extractAmount = (content) => {
  const match = content.match(/(?:RM|MYR|\$|USD|EUR|GBP|INR|Rs\.?|₹)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)/i);
  return match ? Number(match[1].replace(/,/g, "")) : null;
};

const extractTransactionTime = (content) => {
  const isoDateMatch = content.match(/\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?/);
  if (isoDateMatch) {
    return new Date(isoDateMatch[0]).toISOString();
  }

  const timeMatch = content.match(/\b([01]?\d|2[0-3])(?::([0-5]\d))?\s*(AM|PM)?\b/i);
  if (!timeMatch) {
    return new Date().toISOString();
  }

  let hour = Number(timeMatch[1]);
  const minute = Number(timeMatch[2] || 0);
  const meridiem = timeMatch[3]?.toUpperCase();

  if (meridiem === "PM" && hour < 12) hour += 12;
  if (meridiem === "AM" && hour === 12) hour = 0;

  const date = new Date();
  date.setHours(hour, minute, 0, 0);
  return date.toISOString();
};

const extractTransactionType = (content) => {
  const match = TYPE_KEYWORDS.find((item) => item.pattern.test(content));
  return match ? match.value : "UNKNOWN";
};

const extractMerchant = (content) => {
  const merchantPatterns = [
    /(?:at|from|to|merchant)\s+([A-Za-z0-9&.' -]{3,60})(?:\s+on|\s+at|\s+for|\.|,|$)/i,
    /(?:POS|purchase)\s+([A-Za-z0-9&.' -]{3,60})(?:\.|,|$)/i
  ];

  for (const pattern of merchantPatterns) {
    const match = content.match(pattern);
    if (match) {
      return match[1].trim();
    }
  }

  return "Unknown Merchant";
};

const extractLocation = (content) => {
  const match = content.match(/(?:location|in|near)\s+([A-Za-z, ]{3,60})(?:\.|,|$)/i);
  return match ? match[1].trim() : "Unknown";
};

const parseBankEmail = (content) => {
  const amount = extractAmount(content);

  if (!amount) {
    throw new AppError("Could not extract transaction amount from email content.", 422);
  }

  return {
    amount,
    transactionType: extractTransactionType(content),
    transactionTime: extractTransactionTime(content),
    merchant: extractMerchant(content),
    location: extractLocation(content),
    currency: /(?:USD|\$)/i.test(content) ? "USD" : "MYR"
  };
};

module.exports = { parseBankEmail };
