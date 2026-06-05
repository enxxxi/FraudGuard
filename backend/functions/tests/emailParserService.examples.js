const assert = require("node:assert/strict");
const { parseBankEmail } = require("../services/emailParserService");

const examples = [
  {
    name: "Format 1 - transfer to merchant with time and reference",
    payload: {
      sender: "alerts@maybank.com",
      subject: "Transaction Alert",
      body: "RM8500 transferred to ABC Trading at 2:03 AM. Reference TXN12345"
    },
    expected: {
      amount: 8500,
      transactionType: "transfer",
      merchant: "ABC Trading",
      transactionTime: "02:03 AM",
      referenceNumber: "TXN12345",
      location: "Unknown"
    }
  },
  {
    name: "Format 2 - card spend with date and time",
    payload: {
      sender: "alerts@cimb.com",
      subject: "Card Spend Alert",
      body: "You spent RM45.90 at McDonald's on 14 May 2026 12:30 PM"
    },
    expected: {
      amount: 45.9,
      transactionType: "purchase",
      merchant: "McDonald's",
      transactionTime: "12:30 PM",
      referenceNumber: null,
      location: "Unknown"
    }
  },
  {
    name: "Format 3 - transfer completed with reference only",
    payload: {
      sender: "noreply@rhbgroup.com",
      subject: "Transfer Successful",
      body: "Transfer of RM12000 completed successfully. Ref: TXN998877"
    },
    expected: {
      amount: 12000,
      transactionType: "transfer",
      merchant: null,
      transactionTime: null,
      referenceNumber: "TXN998877",
      location: "Unknown"
    }
  },
  {
    name: "Format 4 - debit card purchase merchant only",
    payload: {
      sender: "alerts@publicbank.com.my",
      subject: "Debit Card Purchase",
      body: "Debit card purchase RM89.50 at Shopee"
    },
    expected: {
      amount: 89.5,
      transactionType: "purchase",
      merchant: "Shopee",
      transactionTime: null,
      referenceNumber: null,
      location: "Unknown"
    }
  },
  {
    name: "Missing fields - graceful null output",
    payload: {
      sender: "alerts@bank.example",
      subject: "Account Notice",
      body: "Your account was updated successfully."
    },
    expected: {
      amount: null,
      transactionType: null,
      merchant: null,
      transactionTime: null,
      referenceNumber: null,
      location: "Unknown"
    }
  }
];

const sampleParsedOutputs = examples.map((example) => {
  const result = parseBankEmail(example.payload);

  assert.deepEqual(result.parsedTransaction, example.expected, example.name);
  assert.ok(result.fraudTransaction, `${example.name} should include fraud analysis input`);

  return {
    name: example.name,
    payload: example.payload,
    parsedOutput: result.parsedTransaction,
    extractionMetadata: result.metadata
  };
});

console.log(JSON.stringify(sampleParsedOutputs, null, 2));
