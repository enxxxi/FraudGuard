const { AppError } = require("../utils/AppError");

const DEFAULT_TIMEZONE_OFFSET = "+08:00";

const CURRENCY_MAP = {
  RM: "MYR",
  MYR: "MYR",
  USD: "USD",
  "$": "USD",
  SGD: "SGD",
  EUR: "EUR",
  GBP: "GBP",
  INR: "INR",
  RS: "INR"
};

const TRANSACTION_TYPES = [
  { pattern: /\b(atm|cash withdrawal|withdrawn|withdrawal)\b/i, value: "ATM_WITHDRAWAL" },
  { pattern: /\b(online|ecommerce|e-commerce|web purchase)\b/i, value: "ONLINE_PURCHASE" },
  { pattern: /\b(pos|card|debit card|credit card|purchase|spent|charged)\b/i, value: "CARD_PURCHASE" },
  { pattern: /\b(transfer|sent|duitnow|ibg|instant transfer|third party)\b/i, value: "FUND_TRANSFER" },
  { pattern: /\b(bill|utility|jompay|payment)\b/i, value: "BILL_PAYMENT" },
  { pattern: /\b(credited|refund|deposit|received)\b/i, value: "ACCOUNT_CREDIT" }
];

const MONTHS = {
  jan: 0,
  january: 0,
  feb: 1,
  february: 1,
  mar: 2,
  march: 2,
  apr: 3,
  april: 3,
  may: 4,
  jun: 5,
  june: 5,
  jul: 6,
  july: 6,
  aug: 7,
  august: 7,
  sep: 8,
  sept: 8,
  september: 8,
  oct: 9,
  october: 9,
  nov: 10,
  november: 10,
  dec: 11,
  december: 11
};

const normalizeContent = (content) => content
  .replace(/\r?\n/g, " ")
  .replace(/\s+/g, " ")
  .trim();

const cleanLabelValue = (value) => value
  .replace(/\s+/g, " ")
  .replace(/^[\s:.-]+|[\s:.-]+$/g, "")
  .trim();

const normalizeCurrency = (value) => {
  if (!value) return null;
  const key = value.replace(/\./g, "").toUpperCase();
  return CURRENCY_MAP[key] || key;
};

const isCurrencyToken = (value) => {
  if (!value) return false;
  return Boolean(normalizeCurrency(value) && CURRENCY_MAP[value.replace(/\./g, "").toUpperCase()]);
};

const toAmountNumber = (value) => Number(value.replace(/,/g, ""));

const findAmountCandidates = (content) => {
  const candidates = [];
  const currencyPattern = "(RM|MYR|USD|SGD|EUR|GBP|INR|Rs\\.?|\\$)";
  const amountPattern = "([0-9]{1,3}(?:,[0-9]{3})*(?:\\.[0-9]{1,2})?|[0-9]+(?:\\.[0-9]{1,2})?)";

  const patterns = [
    new RegExp(`\\b(?:amount|amt|transaction amount|purchase of|payment of|transfer of|withdrawal of)\\s*:?\\s*${currencyPattern}?\\s*${amountPattern}\\b`, "gi"),
    new RegExp(`\\b${currencyPattern}\\s*${amountPattern}\\b`, "gi"),
    new RegExp(`\\b${amountPattern}\\s*${currencyPattern}\\b`, "gi")
  ];

  for (const pattern of patterns) {
    let match = pattern.exec(content);

    while (match) {
      const hasLabel = /amount|amt|purchase|payment|transfer|withdrawal/i.test(match[0]);
      const currencyToken = isCurrencyToken(match[1]) ? match[1] : (isCurrencyToken(match[2]) ? match[2] : null);
      const currency = normalizeCurrency(currencyToken);
      const rawAmount = match[2] && !Number.isNaN(Number(match[2].replace(/,/g, ""))) ? match[2] : match[1];

      candidates.push({
        amount: toAmountNumber(rawAmount),
        currency,
        score: (currency ? 2 : 0) + (hasLabel ? 2 : 0),
        index: match.index
      });

      match = pattern.exec(content);
    }
  }

  return candidates
    .filter((candidate) => Number.isFinite(candidate.amount) && candidate.amount > 0)
    .sort((a, b) => b.score - a.score || a.index - b.index);
};

const extractAmountAndCurrency = (content) => {
  const [bestCandidate] = findAmountCandidates(content);

  if (!bestCandidate) {
    return { amount: null, currency: "MYR" };
  }

  return {
    amount: bestCandidate.amount,
    currency: bestCandidate.currency || "MYR"
  };
};

const inferDirection = (content) => {
  if (/\b(credited|refund|refunded|deposit|received|cashback|reversal)\b/i.test(content)) {
    return "CREDIT";
  }

  if (/\b(debited|spent|paid|charged|withdrawn|purchase|sent|transfer to|transfer of)\b/i.test(content)) {
    return "DEBIT";
  }

  return "UNKNOWN";
};

const extractTransactionType = (content) => {
  const match = TRANSACTION_TYPES.find((item) => item.pattern.test(content));
  return match ? match.value : "UNKNOWN";
};

const buildDate = ({ year, month, day, hour = 0, minute = 0, meridiem = null }) => {
  let normalizedHour = Number(hour);
  const normalizedMinute = Number(minute);
  const normalizedMeridiem = meridiem?.toUpperCase();

  if (normalizedMeridiem === "PM" && normalizedHour < 12) normalizedHour += 12;
  if (normalizedMeridiem === "AM" && normalizedHour === 12) normalizedHour = 0;

  const paddedMonth = String(Number(month) + 1).padStart(2, "0");
  const paddedDay = String(Number(day)).padStart(2, "0");
  const paddedHour = String(normalizedHour).padStart(2, "0");
  const paddedMinute = String(normalizedMinute).padStart(2, "0");

  return new Date(`${year}-${paddedMonth}-${paddedDay}T${paddedHour}:${paddedMinute}:00${DEFAULT_TIMEZONE_OFFSET}`);
};

const extractTransactionTime = (content) => {
  const isoDateMatch = content.match(/\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?/);
  if (isoDateMatch) {
    return new Date(isoDateMatch[0]).toISOString();
  }

  const numericDateMatch = content.match(/\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})(?:\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?)?/i);
  if (numericDateMatch) {
    const year = numericDateMatch[3].length === 2 ? `20${numericDateMatch[3]}` : numericDateMatch[3];
    const date = buildDate({
      year,
      month: Number(numericDateMatch[2]) - 1,
      day: numericDateMatch[1],
      hour: numericDateMatch[4] || 0,
      minute: numericDateMatch[5] || 0,
      meridiem: numericDateMatch[6]
    });

    return date.toISOString();
  }

  const textDateMatch = content.match(/\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})(?:\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?)?/i);
  if (textDateMatch) {
    const month = MONTHS[textDateMatch[2].toLowerCase()];

    if (month !== undefined) {
      const date = buildDate({
        year: textDateMatch[3],
        month,
        day: textDateMatch[1],
        hour: textDateMatch[4] || 0,
        minute: textDateMatch[5] || 0,
        meridiem: textDateMatch[6]
      });

      return date.toISOString();
    }
  }

  const timeOnlyMatch = content.match(/\b(?:at|time)\s+(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?\b/i);
  const date = new Date();

  if (timeOnlyMatch) {
    let hour = Number(timeOnlyMatch[1]);
    const minute = Number(timeOnlyMatch[2] || 0);
    const meridiem = timeOnlyMatch[3]?.toUpperCase();

    if (meridiem === "PM" && hour < 12) hour += 12;
    if (meridiem === "AM" && hour === 12) hour = 0;

    date.setHours(hour, minute, 0, 0);
  }

  return date.toISOString();
};

const extractMerchant = (content) => {
  const merchantPatterns = [
    /\b(?:merchant|payee|biller)\s*[:\-]\s*([A-Za-z0-9&.'/@() -]{3,80}?)(?=\s+(?:on|at|location|ref|reference|txn|transaction)\b|[,;]|$)/i,
    /\bcredited\s+to\s+your\s+account\s+from\s+([A-Za-z0-9&.'/@() -]{3,80}?)(?=\s+(?:on|at|location|ref|reference|txn|transaction)\b|[,;]|$)/i,
    /\b(?:at|from|to)\s+([A-Za-z0-9&.'/@() -]{3,80}?)(?=\s+(?:on|at|for|location|ref|reference|txn|transaction)\b|[,;]|$)/i,
    /\b(?:POS|card purchase|online purchase)\s+(?:at\s+)?([A-Za-z0-9&.'/@() -]{3,80}?)(?=[,;]|$)/i
  ];

  for (const pattern of merchantPatterns) {
    const match = content.match(pattern);

    if (match) {
      return cleanLabelValue(match[1]);
    }
  }

  return "Unknown Merchant";
};

const extractLocation = (content) => {
  const locationPatterns = [
    /\b(?:location|place)\s*[:\-]\s*([A-Za-z0-9,.'/@() -]{3,80}?)(?=\s+(?:on|at|ref|reference|txn|transaction)\b|[.;]|$)/i,
    /\b(?:in|near)\s+([A-Za-z,.' -]{3,80}?)(?=\s+(?:on|at|ref|reference|txn|transaction)\b|[.;]|$)/i
  ];

  for (const pattern of locationPatterns) {
    const match = content.match(pattern);

    if (match) {
      return cleanLabelValue(match[1]);
    }
  }

  return "Unknown";
};

const extractReferenceId = (content) => {
  const match = content.match(/\b(?:ref|reference|txn id|transaction id|approval code)\s*[:#-]?\s*([A-Za-z0-9-]{4,40})\b/i);
  return match ? match[1] : null;
};

const buildExtractionWarnings = (transaction) => {
  const warnings = [];

  if (transaction.transactionType === "UNKNOWN") warnings.push("Transaction type could not be confidently detected.");
  if (transaction.direction === "UNKNOWN") warnings.push("Transaction direction could not be confidently detected.");
  if (transaction.merchant === "Unknown Merchant") warnings.push("Merchant could not be confidently detected.");
  if (transaction.location === "Unknown") warnings.push("Location could not be confidently detected.");

  return warnings;
};

const parseBankEmail = (content) => {
  const normalizedContent = normalizeContent(content);
  const { amount, currency } = extractAmountAndCurrency(normalizedContent);

  if (!amount) {
    throw new AppError("Could not extract transaction amount from email content.", 422);
  }

  const transaction = {
    amount,
    currency,
    transactionType: extractTransactionType(normalizedContent),
    direction: inferDirection(normalizedContent),
    transactionTime: extractTransactionTime(normalizedContent),
    merchant: extractMerchant(normalizedContent),
    location: extractLocation(normalizedContent),
    referenceId: extractReferenceId(normalizedContent)
  };

  return {
    ...transaction,
    extractionWarnings: buildExtractionWarnings(transaction)
  };
};

module.exports = { parseBankEmail };
