const DEFAULT_CURRENCY = "MYR";
const DEFAULT_TIMEZONE_OFFSET = "+08:00";

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

const TRANSACTION_TYPE_PATTERNS = [
  { pattern: /\b(debit card purchase|card purchase|purchase|spent|charged)\b/i, standard: "purchase", fraudType: "CARD_PURCHASE", direction: "DEBIT" },
  { pattern: /\b(transferred|transfer|duitnow|ibg|sent)\b/i, standard: "transfer", fraudType: "FUND_TRANSFER", direction: "DEBIT" },
  { pattern: /\b(withdrawal|withdrawn|atm)\b/i, standard: "withdrawal", fraudType: "ATM_WITHDRAWAL", direction: "DEBIT" },
  { pattern: /\b(bill payment|jompay|paid)\b/i, standard: "payment", fraudType: "BILL_PAYMENT", direction: "DEBIT" },
  { pattern: /\b(credited|received|refund|deposit)\b/i, standard: "credit", fraudType: "ACCOUNT_CREDIT", direction: "CREDIT" }
];

const BANK_FORMATS = [
  {
    name: "transfer_to_merchant_time",
    pattern: /\bRM\s*([0-9,]+(?:\.[0-9]{1,2})?)\s+(?:was\s+)?transferred\s+to\s+(.+?)\s+at\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\b/i,
    extract: (match) => ({
      amount: toAmount(match[1]),
      transactionType: "transfer",
      merchant: cleanValue(match[2]),
      transactionTime: normalizeDisplayTime(match[3])
    })
  },
  {
    name: "spent_at_merchant_datetime",
    pattern: /\byou\s+spent\s+RM\s*([0-9,]+(?:\.[0-9]{1,2})?)\s+at\s+(.+?)\s+on\s+(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\b/i,
    extract: (match) => ({
      amount: toAmount(match[1]),
      transactionType: "purchase",
      merchant: cleanValue(match[2]),
      transactionDate: cleanValue(match[3]),
      transactionTime: normalizeDisplayTime(match[4])
    })
  },
  {
    name: "transfer_of_amount_ref",
    pattern: /\btransfer\s+of\s+RM\s*([0-9,]+(?:\.[0-9]{1,2})?)\s+completed\b/i,
    extract: (match) => ({
      amount: toAmount(match[1]),
      transactionType: "transfer"
    })
  },
  {
    name: "card_purchase_at_merchant",
    pattern: /\bdebit\s+card\s+purchase\s+RM\s*([0-9,]+(?:\.[0-9]{1,2})?)\s+at\s+(.+?)(?=\s+(?:on|at|ref|reference)\b|[.;]|$)/i,
    extract: (match) => ({
      amount: toAmount(match[1]),
      transactionType: "purchase",
      merchant: cleanValue(match[2])
    })
  }
];

const normalizeContent = (value) => String(value || "")
  .replace(/\r?\n/g, " ")
  .replace(/\s+/g, " ")
  .trim();

const cleanEmailAddress = (value) => {
  const text = normalizeContent(value);
  const markdownMatch = text.match(/\[([^\]]+)]\(mailto:[^)]+\)/i);
  return markdownMatch ? markdownMatch[1] : text;
};

const cleanValue = (value) => normalizeContent(value)
  .replace(/^[\s:.-]+|[\s:.-]+$/g, "")
  .replace(/\s+(?:successfully|completed)$/i, "")
  .trim();

const toAmount = (value) => {
  const amount = Number(String(value || "").replace(/,/g, ""));
  return Number.isFinite(amount) ? amount : null;
};

const normalizeDisplayTime = (value) => {
  const match = normalizeContent(value).match(/\b(\d{1,2})(?::(\d{2}))\s*(AM|PM)?\b/i);

  if (!match) {
    return null;
  }

  const hour = String(Number(match[1])).padStart(2, "0");
  const minute = String(Number(match[2] || 0)).padStart(2, "0");
  const meridiem = match[3] ? ` ${match[3].toUpperCase()}` : "";

  return `${hour}:${minute}${meridiem}`;
};

const buildIsoDateTime = (datePart, timePart) => {
  if (!timePart) {
    return null;
  }

  const timeMatch = timePart.match(/\b(\d{1,2}):(\d{2})\s*(AM|PM)?\b/i);
  if (!timeMatch) {
    return null;
  }

  let hour = Number(timeMatch[1]);
  const minute = Number(timeMatch[2]);
  const meridiem = timeMatch[3]?.toUpperCase();

  if (meridiem === "PM" && hour < 12) hour += 12;
  if (meridiem === "AM" && hour === 12) hour = 0;

  const now = new Date();
  let day = now.getDate();
  let month = now.getMonth();
  let year = now.getFullYear();

  if (datePart) {
    const dateStr = normalizeContent(datePart);
    const isoMatch = dateStr.match(/\b(\d{4})-(\d{2})-(\d{2})\b/);
    if (isoMatch) {
      year = Number(isoMatch[1]);
      month = Number(isoMatch[2]) - 1;
      day = Number(isoMatch[3]);
    } else {
      const dateMatch = dateStr.match(/\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b/i);
      if (dateMatch) {
        day = Number(dateMatch[1]);
        month = MONTHS[dateMatch[2].toLowerCase()];
        year = Number(dateMatch[3]);
      }
    }
  }

  if (month === undefined || month < 0 || month > 11) {
    return null;
  }

  const paddedMonth = String(month + 1).padStart(2, "0");
  const paddedDay = String(day).padStart(2, "0");
  const paddedHour = String(hour).padStart(2, "0");
  const paddedMinute = String(minute).padStart(2, "0");
  const date = new Date(`${year}-${paddedMonth}-${paddedDay}T${paddedHour}:${paddedMinute}:00${DEFAULT_TIMEZONE_OFFSET}`);

  return Number.isNaN(date.getTime()) ? null : date.toISOString();
};

const extractAmount = (content) => {
  const patterns = [
    /\b(?:amount|amt|purchase|spent|transfer\s+of|payment\s+of)\s*:?\s*RM\s*([0-9,]+(?:\.[0-9]{1,2})?)\b/i,
    /\bRM\s*([0-9,]+(?:\.[0-9]{1,2})?)\b/i
  ];

  for (const pattern of patterns) {
    const match = content.match(pattern);

    if (match) {
      return toAmount(match[1]);
    }
  }

  return null;
};

const extractTransactionType = (content) => {
  const match = TRANSACTION_TYPE_PATTERNS.find((item) => item.pattern.test(content));

  return {
    transactionType: match?.standard || null,
    fraudType: match?.fraudType || "UNKNOWN",
    direction: match?.direction || "UNKNOWN"
  };
};

const extractMerchant = (content) => {
  const patterns = [
    /\btransferred\s+to\s+(.+?)\s+at\s+\d{1,2}:\d{2}\s*(?:AM|PM)\b/i,
    /\b(?:spent|purchase|charged)\s+RM\s*[0-9,]+(?:\.[0-9]{1,2})?\s+at\s+(.+?)(?=\s+on\s+\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\s+(?:ref|reference)\b|[.;]|$)/i,
    /\bat\s+(.+?)(?=\s+(?:on|ref|reference|time)\b|[.;]|$)/i,
    /\bto\s+(.+?)(?=\s+(?:on|at|ref|reference)\b|[.;]|$)/i,
    /\bmerchant\s*[:\-]\s*(.+?)(?=\s+(?:on|at|ref|reference)\b|[.;]|$)/i
  ];

  for (const pattern of patterns) {
    const match = content.match(pattern);

    if (match) {
      return cleanValue(match[1]);
    }
  }

  return null;
};

const extractTransactionTime = (content) => {
  const timePatterns = [
    /\bon\s+\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\b/i,
    /\b(?:at|time)\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?)\b/i,
    /\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b/i
  ];

  for (const pattern of timePatterns) {
    const match = content.match(pattern);

    if (match) {
      return normalizeDisplayTime(match[1]);
    }
  }

  return null;
};

const extractTransactionDate = (content) => {
  const match = content.match(/\bon\s+(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b/i);
  if (match) return cleanValue(match[1]);

  const matchIso = content.match(/\bon\s+(\d{4}-\d{2}-\d{2})\b/i);
  if (matchIso) return cleanValue(matchIso[1]);

  const matchIsoPlain = content.match(/\b(\d{4}-\d{2}-\d{2})\b/i);
  if (matchIsoPlain) return cleanValue(matchIsoPlain[1]);

  return null;
};

const extractReferenceNumber = (content) => {
  const match = content.match(/\b(?:reference|ref|txn|transaction\s+id|approval\s+code)\b\s*[:#-]?\s*([A-Z0-9-]{4,40})\b/i);
  return match ? match[1].toUpperCase() : null;
};

const extractLocation = (content) => {
  // Pattern 1: location/country followed by colon/dash
  let match = content.match(/\b(?:location|country)\s*[:\-]\s*([A-Za-z\s\.-]{2,50})/i);
  if (match) {
    const val = match[1].trim();
    if (val && val.toLowerCase() !== "unknown") {
      return val;
    }
  }

  // Pattern 2: location/country in/of/at [Location]
  match = content.match(/\b(?:location|country)\s+(?:in|of|at)\s+([A-Za-z\s\.-]{2,50})/i);
  if (match) {
    const val = match[1].trim();
    if (val && val.toLowerCase() !== "unknown") {
      return val;
    }
  }

  // Pattern 3: recipient in/at [Location]
  match = content.match(/\brecipient\s+(?:in|at)\s+([A-Za-z\s\.-]{2,50})/i);
  if (match) {
    const val = match[1].trim();
    if (val && val.toLowerCase() !== "unknown") {
      return val;
    }
  }

  return "Unknown";
};

const runFormatExtractors = (content) => {
  for (const format of BANK_FORMATS) {
    const match = content.match(format.pattern);

    if (match) {
      return {
        matchedFormat: format.name,
        fields: format.extract(match)
      };
    }
  }

  return {
    matchedFormat: "generic_regex",
    fields: {}
  };
};

const buildWarnings = (parsed) => {
  const warnings = [];

  if (parsed.amount === null) warnings.push("Amount could not be extracted.");
  if (parsed.transactionType === null) warnings.push("Transaction type could not be extracted.");
  if (parsed.merchant === null) warnings.push("Merchant could not be extracted.");
  if (parsed.transactionTime === null) warnings.push("Transaction time could not be extracted.");
  if (parsed.referenceNumber === null) warnings.push("Reference number could not be extracted.");

  return warnings;
};

const buildFraudTransaction = (parsed, inferred) => ({
  amount: parsed.amount,
  currency: parsed.currency,
  transactionType: inferred.fraudType,
  direction: inferred.direction,
  merchant: parsed.merchant || "Unknown Merchant",
  location: parsed.location || "Unknown",
  transactionTime: buildIsoDateTime(parsed.transactionDate, parsed.transactionTime) || new Date().toISOString(),
  referenceId: parsed.referenceNumber,
  extractionWarnings: parsed.extractionWarnings
});

const parseBankEmail = (emailInput) => {
  const email = typeof emailInput === "string"
    ? { sender: null, subject: null, body: emailInput }
    : emailInput || {};
  const sender = cleanEmailAddress(email.sender);
  const subject = normalizeContent(email.subject);
  const body = normalizeContent(email.body || email.emailContent);
  const content = normalizeContent(`${subject} ${body}`);
  const { matchedFormat, fields } = runFormatExtractors(content);
  const inferred = extractTransactionType(content);

  const parsed = {
    amount: fields.amount ?? extractAmount(content),
    transactionType: fields.transactionType || inferred.transactionType,
    merchant: fields.merchant ?? extractMerchant(content),
    transactionTime: fields.transactionTime ?? extractTransactionTime(content),
    referenceNumber: fields.referenceNumber ?? extractReferenceNumber(content),
    location: extractLocation(content),
    currency: DEFAULT_CURRENCY,
    sender: sender || null,
    subject: subject || null,
    transactionDate: fields.transactionDate ?? extractTransactionDate(content),
    matchedFormat
  };

  parsed.extractionWarnings = buildWarnings(parsed);

  return {
    parsedTransaction: {
      amount: parsed.amount,
      transactionType: parsed.transactionType,
      merchant: parsed.merchant,
      transactionTime: parsed.transactionTime,
      referenceNumber: parsed.referenceNumber,
      location: parsed.location
    },
    metadata: {
      sender: parsed.sender,
      subject: parsed.subject,
      currency: parsed.currency,
      transactionDate: parsed.transactionDate,
      matchedFormat: parsed.matchedFormat,
      extractionWarnings: parsed.extractionWarnings
    },
    fraudTransaction: buildFraudTransaction(parsed, inferred)
  };
};

module.exports = {
  parseBankEmail,
  parseEmailForTransaction: parseBankEmail
};
