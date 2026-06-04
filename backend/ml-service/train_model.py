import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Define the expected feature columns in the exact order
FEATURE_COLUMNS = [
    "account_age_days",
    "credit_score_band",
    "kyc_level",
    "avg_monthly_spend",
    "merchant_risk_score",
    "transaction_amount",
    "is_international",
    "ip_risk_score",
    "txn_count_1h",
    "txn_count_24h",
    "failed_txn_count_24h",
    "geo_distance_from_last_txn",
    "amount_deviation_from_user_mean",
    "hour",
    "day",
    "month",
    "is_after_june",
    "payment_channel_card",
    "payment_channel_upi",
    "payment_channel_wallet",
    "device_type_mobile",
    "device_type_tablet"
]

def main():
    print("Generating synthetic dataset...")
    np.random.seed(42)
    n_samples = 200
    
    # Generate random features
    data = {
        "account_age_days": np.random.randint(30, 3650, n_samples),
        "credit_score_band": np.random.randint(1, 6, n_samples),
        "kyc_level": np.random.randint(1, 4, n_samples),
        "avg_monthly_spend": np.random.uniform(500, 20000, n_samples),
        "merchant_risk_score": np.random.choice([0.15, 0.25, 0.5, 0.8], n_samples),
        "transaction_amount": np.random.exponential(scale=1500, size=n_samples),
        "is_international": np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        "ip_risk_score": np.random.choice([0.15, 0.6], n_samples, p=[0.8, 0.2]),
        "txn_count_1h": np.random.randint(0, 5, n_samples),
        "txn_count_24h": np.random.randint(1, 15, n_samples),
        "failed_txn_count_24h": np.random.randint(0, 3, n_samples),
        "geo_distance_from_last_txn": np.random.uniform(0.1, 500, n_samples),
        "amount_deviation_from_user_mean": np.random.normal(0, 500, n_samples),
        "hour": np.random.randint(0, 24, n_samples),
        "day": np.random.randint(1, 29, n_samples),
        "month": np.random.randint(1, 13, n_samples),
        "is_after_june": np.random.choice([0, 1], n_samples),
        "payment_channel_card": np.random.choice([0, 1], n_samples),
        "payment_channel_upi": np.random.choice([0, 1], n_samples),
        "payment_channel_wallet": np.random.choice([0, 1], n_samples),
        "device_type_mobile": np.random.choice([0, 1], n_samples),
        "device_type_tablet": np.random.choice([0, 1], n_samples)
    }
    
    # Ensure mutually exclusive device types (simplification)
    for i in range(n_samples):
        if data["device_type_mobile"][i] == 1 and data["device_type_tablet"][i] == 1:
            data["device_type_tablet"][i] = 0
            
    df = pd.DataFrame(data)
    
    # Simple rule-based label generation for training
    # Fraud condition: very high amount OR (late night & high merchant risk score & high amount deviation)
    is_fraud = []
    for idx, row in df.iterrows():
        fraud_prob = 0.05
        if row["transaction_amount"] >= 5000:
            fraud_prob += 0.45
        if 0 <= row["hour"] < 5:
            fraud_prob += 0.25
        if row["merchant_risk_score"] >= 0.7:
            fraud_prob += 0.20
        if row["ip_risk_score"] >= 0.5:
            fraud_prob += 0.15
        
        is_fraud.append(1 if fraud_prob >= 0.5 else 0)
        
    df["is_fraud"] = is_fraud
    
    # Train the Random Forest model
    print("Training Random Forest classifier...")
    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]
    
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)
    
    # Save the model and columns
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "fraud_model.pkl")
    cols_path = os.path.join(base_dir, "feature_columns.pkl")
    
    joblib.dump(clf, model_path)
    joblib.dump(FEATURE_COLUMNS, cols_path)
    
    print(f"Saved model to: {model_path}")
    print(f"Saved feature columns to: {cols_path}")
    print("Training complete.")

if __name__ == "__main__":
    main()
