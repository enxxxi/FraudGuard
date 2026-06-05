require('dotenv').config();

const url = process.env.ML_SERVICE_URL;
console.log('ML_SERVICE_URL:', JSON.stringify(url));
if (url) {
  console.log('Length:', url.length);
  for (let i = 0; i < url.length; i++) {
    console.log(`Char at ${i}: ${url.charCodeAt(i)} (${url[i]})`);
  }
} else {
  console.log('ML_SERVICE_URL is not defined in env');
}
