const router = require("express").Router();
const { predictFraud } = require("../controllers/fraudController");

router.post("/predict", predictFraud);

module.exports = router;
