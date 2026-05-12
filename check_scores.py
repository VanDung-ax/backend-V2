import pandas as pd
import requests
import json

df = pd.read_csv("dataset_sinhvien_moi.csv", encoding="utf-8-sig")

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

X = df[FEATURE_COLUMNS]
records = X.to_dict(orient="records")

print("Calling AI API...")
response = requests.post("https://ai-early-warning-system.onrender.com/api/predict_batch", json=records, timeout=180)
ai_results = response.json()
if isinstance(ai_results, dict):
    ai_results = ai_results.get("results", [])

scores = [r.get("risk_score", 0) for r in ai_results]
print(f"Total: {len(scores)}")
print(f"Min: {min(scores):.4f}")
print(f"Max: {max(scores):.4f}")
print(f"Mean: {sum(scores)/len(scores):.4f}")

# Distribution
bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
import numpy as np
counts, edges = np.histogram(scores, bins=bins)
for i in range(len(counts)):
    print(f"  {edges[i]:.1f}-{edges[i+1]:.1f}: {counts[i]} students")

# Check risk levels
levels = [r.get("risk_level", "?") for r in ai_results]
from collections import Counter
print(f"\nRisk levels: {dict(Counter(levels))}")
