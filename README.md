# FraudGuard

**ML-Powered Bank Transaction Fraud Detection System**

## Overview

FraudGuard is an intelligent fraud detection dashboard that analyzes bank transaction email notifications to identify suspicious financial activities in real time. The system uses machine learning to predict fraud probability, assign risk levels (LOW / MEDIUM / HIGH), and provide explainable analysis of suspicious behavior.

## Key Features

✅ **Email Notification Fraud Detection** — Process incoming bank alerts with automatic risk scoring  
✅ **Transaction Risk Prediction** — Classify transactions as LOW, MEDIUM, or HIGH-risk  
✅ **Fraud Probability Scoring** — ML-based fraud likelihood (0–100%)  
✅ **Explainable Fraud Analysis** — Understand *why* a transaction is flagged  
✅ **Fraud Monitoring Dashboard** — Monitor critical alerts and trends  
✅ **Data Visualization & Reporting** — Charts, risk distribution, fraud score trends  

## Dashboard Pages

- **🏠 Home** — KPI metrics & critical alerts at a glance
- **📧 Incoming Alerts** — Real-time bank email notifications with risk analysis
- **🔍 Transaction Analysis** — Detailed transaction table & risk distribution
- **📈 Analytics** — Fraud trends, score distribution, transaction type heatmap
- **⚙️ Settings** — Configure detection thresholds, alert sensitivity, data retention

## System Flow

```
Bank Email Notification
       ↓
Transaction Information Extraction
       ↓
Fraud Detection ML Model
       ↓
Risk Prediction & Analysis (Fraud Score + Risk Level)
       ↓
Dashboard / User Alert
```

## Getting Started

### Prerequisites
- Python 3.9+
- pip

### Installation

```powershell
# Create virtual environment (recommended)
py -3 -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Or allow execution if blocked:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Upgrade pip & install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run the Dashboard

```powershell
python -m streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

### Alternative (Without Virtual Environment)

```powershell
py -3 -m pip install --user -r requirements.txt
py -3 -m streamlit run app.py
```

## Demo Data

The dashboard includes **simulated bank transactions** with:
- 25 sample transactions (40% fraud rate for demo)
- Realistic transaction patterns (amount, time, location, type)
- ML-based fraud scores (0.0–1.0 probability)
- Explainable fraud reasons (high amount, late-night, etc.)

**No real data** — all data is synthetic for demonstration.

## Example Use Case

📧 **Email Received:**
```
"₹8,500 transferred at 2:03 AM"
```

↓

**System Analysis:**
```
Risk Level: HIGH
Fraud Probability: 92%

Reasons:
• Unusually high transaction amount
• Suspicious late-night transfer
• Abnormal spending behavior
```

## Tech Stack

- **Streamlit** — Interactive web dashboard
- **Pandas** — Data processing
- **Plotly** — Interactive visualizations
- **NumPy** — Numerical computations
- **Scikit-learn** — ML utilities

## Project Structure

```
FraudGuard/
├── app.py                 # Main Streamlit dashboard
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Future Enhancements

- 🔌 Real bank API integration (Plaid, etc.)
- 🤖 Advanced ML models (Random Forest, XGBoost, Neural Networks)
- 📧 Email notification processing pipeline
- 💾 Database integration (PostgreSQL, MongoDB)
- 🔔 Real-time alerting system
- 📱 Mobile app support
- 🔐 Authentication & role-based access control

## License

Open source — use freely for educational and commercial purposes.

## Contact & Support

For issues, questions, or feature requests, please open an issue or contact the development team.

---

**FraudGuard v1.0** — Making fraud detection intelligent, explainable, and actionable.