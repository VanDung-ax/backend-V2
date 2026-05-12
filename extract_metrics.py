"""
Script trich xuat Model Evaluation Metrics
Dung CatBoost + SMOTE tren dataset_sinhvien_moi.csv
Ket qua luu file model_metrics.json de frontend hien thi

Chay:  python extract_metrics.py
"""
import pandas as pd
import numpy as np
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
from catboost import CatBoostClassifier

# === BUOC 1: Doc du lieu ===
print("=" * 60)
print("BUOC 1: Doc du lieu")
print("=" * 60)

df = pd.read_csv("dataset_sinhvien_moi.csv", encoding="utf-8-sig")
print(f"Tong so mau: {len(df)}")

# === BUOC 2: Chuan bi 13 features ===
print("\n" + "=" * 60)
print("BUOC 2: Chuan bi 13 features")
print("=" * 60)

FEATURE_COLUMNS = [
    "thoi_gian_tu_hoc", "chuyen_can", "diem_qua_trinh", "hoan_thanh_bai_tap",
    "loai_mon_hoc", "tai_lieu_on_tap", "hinh_thuc_thi", "tre_hoc_phi",
    "ho_tro", "tre_hoc", "hoc_nhom", "lam_them", "co_kinh_nghiem"
]

NUMERIC_COLS = ["thoi_gian_tu_hoc", "chuyen_can", "diem_qua_trinh", "hoan_thanh_bai_tap", "tre_hoc"]
TEXT_COLS = ["loai_mon_hoc", "tai_lieu_on_tap", "hinh_thuc_thi", "tre_hoc_phi",
             "ho_tro", "hoc_nhom", "lam_them", "co_kinh_nghiem"]

for col in NUMERIC_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
for col in TEXT_COLS:
    df[col] = df[col].fillna("Khong").astype(str)

X = df[FEATURE_COLUMNS].copy()

# === BUOC 3: Lay nhan tu AI API ===
print("\n" + "=" * 60)
print("BUOC 3: Goi AI API de lay nhan thuc te")
print("=" * 60)

import requests

AI_URL = "https://ai-early-warning-system.onrender.com/api/predict_batch"

print("Dang goi AI API...")
records = X.to_dict(orient="records")

try:
    response = requests.post(AI_URL, json=records, timeout=180)
    if response.status_code == 200:
        ai_results = response.json()
        if isinstance(ai_results, dict):
            ai_results = ai_results.get("results", [])
        
        # Dung risk_level de tao nhan nhi phan
        # CAO (Nguy hiem) = 1 (rui ro rot mon)
        # TRUNG BINH + THAP = 0 (an toan)
        labels = []
        for r in ai_results:
            level = r.get("risk_level", "")
            if "CAO" in level.upper() or "NGUY" in level.upper():
                labels.append(1)
            else:
                labels.append(0)
        
        df["label"] = labels
        print(f"Lay nhan tu AI thanh cong!")
        print(f"  Rui ro (1): {sum(labels)}")
        print(f"  An toan (0): {len(labels) - sum(labels)}")
    else:
        raise Exception(f"API error: {response.status_code}")
except Exception as e:
    print(f"Khong the goi AI API: {e}")
    print("Su dung nhan dua tren rules thay the...")
    
    risk_points = np.zeros(len(df))
    risk_points += (df["chuyen_can"] < 50).astype(float) * 2
    risk_points += (df["diem_qua_trinh"] < 5).astype(float) * 2.5
    risk_points += (df["hoan_thanh_bai_tap"] < 50).astype(float) * 1.5
    risk_points += (df["thoi_gian_tu_hoc"] < 30).astype(float) * 1
    risk_points += (df["tre_hoc"] > 40).astype(float) * 1
    risk_points += (df["tre_hoc_phi"] == "Co").astype(float) * 1
    risk_points += (df["ho_tro"] == "Khong").astype(float) * 0.5
    risk_points += (df["tai_lieu_on_tap"] == "Khong").astype(float) * 0.5
    
    df["label"] = (risk_points >= 4).astype(int)
    print(f"  Rui ro (1): {(df['label']==1).sum()}")
    print(f"  An toan (0): {(df['label']==0).sum()}")

y = df["label"]

# === BUOC 4: Encode categorical features ===
print("\n" + "=" * 60)
print("BUOC 4: Encode categorical -> numeric")
print("=" * 60)

label_encoders = {}
X_encoded = X.copy()
for col in TEXT_COLS:
    le = LabelEncoder()
    X_encoded[col] = le.fit_transform(X_encoded[col])
    label_encoders[col] = le
    print(f"  {col}: {dict(zip(le.classes_, le.transform(le.classes_)))}")

# === BUOC 5: Train/Test Split ===
print("\n" + "=" * 60)
print("BUOC 5: Chia Train/Test (80/20)")
print("=" * 60)

X_train, X_test, y_train, y_test = train_test_split(
    X_encoded, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train)} mau | Test: {len(X_test)} mau")
print(f"Train label 0: {(y_train==0).sum()}, label 1: {(y_train==1).sum()}")
print(f"Test  label 0: {(y_test==0).sum()}, label 1: {(y_test==1).sum()}")

# === BUOC 6: Ap dung SMOTE (chi tren Train) ===
print("\n" + "=" * 60)
print("BUOC 6: Ap dung SMOTE (chi tren tap TRAIN)")
print("=" * 60)

print(f"TRUOC SMOTE - label 0: {(y_train==0).sum()}, label 1: {(y_train==1).sum()}")

smote = SMOTE(random_state=42)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

y_train_sm_series = pd.Series(y_train_sm)
print(f"SAU SMOTE   - label 0: {(y_train_sm_series==0).sum()}, label 1: {(y_train_sm_series==1).sum()}")
print(f"(Tap Test KHONG bi SMOTE - giu nguyen {len(X_test)} mau)")

# === BUOC 7: Train CatBoost ===
print("\n" + "=" * 60)
print("BUOC 7: Train CatBoost Classifier")
print("=" * 60)

model = CatBoostClassifier(
    iterations=500,
    learning_rate=0.05,
    depth=6,
    eval_metric="F1",
    random_seed=42,
    verbose=100
)

model.fit(X_train_sm, y_train_sm)
print("Train xong!")

# === BUOC 8: Danh gia tren tap TEST ===
print("\n" + "=" * 60)
print("BUOC 8: DANH GIA MODEL TREN TAP TEST")
print("=" * 60)

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
roc_auc = roc_auc_score(y_test, y_pred_proba)
cm = confusion_matrix(y_test, y_pred)

print(f"\n{'='*40}")
print(f"  ACCURACY  : {accuracy:.4f}  ({accuracy*100:.2f}%)")
print(f"  PRECISION : {precision:.4f}  ({precision*100:.2f}%)")
print(f"  RECALL    : {recall:.4f}  ({recall*100:.2f}%)")
print(f"  F1-SCORE  : {f1:.4f}  ({f1*100:.2f}%)")
print(f"  ROC-AUC   : {roc_auc:.4f}  ({roc_auc*100:.2f}%)")
print(f"{'='*40}")

print(f"\nConfusion Matrix:")
print(f"                  Predicted")
print(f"                  AN TOAN  RUI RO")
print(f"  Actual AN TOAN   {cm[0][0]:>5}   {cm[0][1]:>5}")
print(f"  Actual RUI RO    {cm[1][0]:>5}   {cm[1][1]:>5}")

print(f"\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["An toan", "Rui ro"]))

# === BUOC 9: Feature Importance ===
print("\n" + "=" * 60)
print("BUOC 9: Feature Importance")
print("=" * 60)

importances = model.get_feature_importance()
feature_imp = sorted(
    zip(FEATURE_COLUMNS, importances),
    key=lambda x: x[1], reverse=True
)

max_imp = max(importances)
for name, imp in feature_imp:
    bar = "#" * int(imp / max_imp * 30)
    print(f"  {name:<23} {imp:>8.2f}%  {bar}")

# === BUOC 10: Luu ket qua JSON ===
print("\n" + "=" * 60)
print("BUOC 10: Luu ket qua vao model_metrics.json")
print("=" * 60)

metrics_data = {
    "model_name": "CatBoost Classifier",
    "balancing": "SMOTE (Synthetic Minority Over-sampling Technique)",
    "dataset_size": int(len(df)),
    "train_size": int(len(X_train)),
    "test_size": int(len(X_test)),
    "train_size_after_smote": int(len(X_train_sm)),
    "features_count": 13,
    "features": FEATURE_COLUMNS,
    "class_distribution": {
        "before_smote": {
            "safe": int((y_train==0).sum()),
            "risk": int((y_train==1).sum())
        },
        "after_smote": {
            "safe": int((y_train_sm_series==0).sum()),
            "risk": int((y_train_sm_series==1).sum())
        }
    },
    "metrics": {
        "accuracy": round(float(accuracy * 100), 2),
        "precision": round(float(precision * 100), 2),
        "recall": round(float(recall * 100), 2),
        "f1_score": round(float(f1 * 100), 2),
        "roc_auc": round(float(roc_auc * 100), 2)
    },
    "confusion_matrix": {
        "true_negative": int(cm[0][0]),
        "false_positive": int(cm[0][1]),
        "false_negative": int(cm[1][0]),
        "true_positive": int(cm[1][1])
    },
    "feature_importance": [
        {"name": name, "importance": round(float(imp), 2)}
        for name, imp in feature_imp
    ]
}

with open("model_metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics_data, f, ensure_ascii=False, indent=2)

print("Da luu vao model_metrics.json")
print("\nHOAN TAT!")
