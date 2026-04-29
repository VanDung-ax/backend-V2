"""
Routes dự báo rủi ro học tập — sử dụng database student_risk_v2
AI Endpoint: https://ai-early-warning-system.onrender.com/api/predict_batch
13 thuộc tính đầu vào: thoi_gian_tu_hoc, chuyen_can, diem_qua_trinh,
hoan_thanh_bai_tap, loai_mon_hoc, tai_lieu_on_tap, hinh_thuc_thi,
tre_hoc_phi, ho_tro, tre_hoc, hoc_nhom, lam_them, co_kinh_nghiem
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import pandas as pd
import io
import requests
import json
from typing import Optional, List
from pydantic import BaseModel
import hashlib

from app.database_v2 import get_db_v2
from app.models.student_risk_v2 import (
    SinhVien2, Khoa2, Lop2, MonHoc2,
    RiskFeatures2, PredictionBatch2, PredictionResult2,
    TaiKhoan2
)
from app.services.learning_engine import generate_learning_path, generate_exercises

router = APIRouter(prefix="/api/v2", tags=["Dự báo & Tái dự báo"])

# ── Địa chỉ AI ────────────────────────────────────────────────────
AI_PREDICT_BATCH_URL = "https://ai-early-warning-system.onrender.com/api/predict_batch"
AI_PREDICT_SINGLE_URL = "https://ai-early-warning-system.onrender.com/api/predict"

# ── 13 cột đặc trưng gửi cho AI ───────────────────────────────────
FEATURE_COLUMNS = [
    "thoi_gian_tu_hoc", "chuyen_can", "diem_qua_trinh", "hoan_thanh_bai_tap",
    "loai_mon_hoc", "tai_lieu_on_tap", "hinh_thuc_thi", "tre_hoc_phi",
    "ho_tro", "tre_hoc", "hoc_nhom", "lam_them", "co_kinh_nghiem"
]

NUMERIC_COLS = ["thoi_gian_tu_hoc", "chuyen_can", "diem_qua_trinh", "hoan_thanh_bai_tap", "tre_hoc"]
TEXT_COLS = ["loai_mon_hoc", "tai_lieu_on_tap", "hinh_thuc_thi", "tre_hoc_phi",
             "ho_tro", "hoc_nhom", "lam_them", "co_kinh_nghiem"]

# ── Cột bắt buộc trong CSV ────────────────────────────────────────
CSV_REQUIRED_COLS = ["MSSV", "Khoa"] + FEATURE_COLUMNS


# ─────────────────────────────────────────────────────────────────
#  1. UPLOAD CSV & DỰ BÁO HÀNG LOẠT (Phòng đào tạo)
# ─────────────────────────────────────────────────────────────────
@router.post("/upload-predict")
async def upload_and_predict(
    file: UploadFile = File(...),
    user_id: Optional[int] = None,
    ten_dot: Optional[str] = None,
    db: Session = Depends(get_db_v2)
):
    """Upload file CSV → gọi AI → lưu kết quả toàn bộ vào DB student_risk_v2"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .csv")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc file CSV: {str(e)}")

    # Kiểm tra cột bắt buộc
    missing_cols = [c for c in CSV_REQUIRED_COLS if c not in df.columns]
    if "HoTen" not in df.columns and "Họ Tên" not in df.columns:
        missing_cols.append("HoTen / Họ Tên")
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"File thiếu các cột: {missing_cols}")

    # Xử lý giá trị rỗng
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in TEXT_COLS:
        if col in df.columns:
            df[col] = df[col].fillna("Không").astype(str)

    # Chuẩn bị payload gửi AI
    records_to_send = df[FEATURE_COLUMNS].to_dict(orient="records")

    # Gọi AI
    try:
        response = requests.post(AI_PREDICT_BATCH_URL, json=records_to_send, timeout=120)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"AI Server lỗi ({response.status_code}): {response.text}"
            )
        ai_data = response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối tới AI: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý AI: {str(e)}")

    # Lưu vào DB
    try:
        # Tạo batch mới
        batch = PredictionBatch2(
            ten_dot=ten_dot or f"Đợt dự báo {file.filename}",
            mo_ta=f"Upload từ file: {file.filename}",
            uploaded_by=user_id
        )
        db.add(batch)
        db.flush()

        # Lấy results từ AI — chấp nhận cả list trực tiếp và {results: [...]}
        ai_results = ai_data if isinstance(ai_data, list) else ai_data.get("results", [])

        for idx, row in df.iterrows():
            mssv = str(row["MSSV"]).strip()

            # Khoa
            ten_khoa = str(row.get("Khoa", "")).strip()
            khoa = db.query(Khoa2).filter(Khoa2.TenKhoa == ten_khoa).first()
            if not khoa:
                khoa = Khoa2(MaKhoa=ten_khoa[:20], TenKhoa=ten_khoa)
                db.add(khoa)
                db.flush()

            # Lớp (tùy chọn)
            lop_db = None
            ma_lop_raw = row.get("Lop") or row.get("Lớp")
            if pd.notna(ma_lop_raw) and str(ma_lop_raw).strip():
                ma_lop_str = str(ma_lop_raw).strip()
                lop_db = db.query(Lop2).filter(Lop2.MaLop == ma_lop_str).first()
                if not lop_db:
                    lop_db = Lop2(MaLop=ma_lop_str[:20], TenLop=ma_lop_str, MaKhoa=khoa.MaKhoa)
                    db.add(lop_db)
                    db.flush()

            # Môn học (tự động thêm)
            ten_mon = str(row.get("Môn học") or row.get("MonHoc") or "").strip()
            if ten_mon:
                mon_db = db.query(MonHoc2).filter(MonHoc2.TenMonHoc == ten_mon).first()
                if not mon_db:
                    loai_mon = str(row.get("loai_mon_hoc", "")).strip()
                    nganh_sv = str(row.get("Nganh") or row.get("Ngành") or "").strip()
                    
                    mon_db = MonHoc2(
                        MaMonHoc=ten_mon[:50],  # Dùng tên môn làm mã môn (giống cách làm của Khoa, Lớp)
                        TenMonHoc=ten_mon,
                        LoaiMonHoc=loai_mon,
                        Nganh=nganh_sv if loai_mon.lower() == "chuyên ngành" else None
                    )
                    db.add(mon_db)
                    db.flush()

            # Sinh viên
            sv = db.query(SinhVien2).filter(SinhVien2.MSSV == mssv).first()
            if not sv:
                sv = SinhVien2(
                    MSSV=mssv,
                    HoTen=str(row.get("HoTen") or row.get("Họ Tên") or ""),
                    MaKhoa=khoa.MaKhoa,
                    Nganh=str(row.get("Nganh") or row.get("Ngành") or ""),
                    MaLop=lop_db.MaLop if lop_db else None
                )
                db.add(sv)
                db.flush()
                
                # Tạo tài khoản mặc định nếu chưa có
                acc = db.query(TaiKhoan2).filter(TaiKhoan2.username == mssv).first()
                if not acc:
                    hashed_pw = hashlib.sha256("1234".encode()).hexdigest()
                    new_acc = TaiKhoan2(
                        username=mssv,
                        password=hashed_pw,
                        role="sinhvien",
                        MSSV_LienKet=mssv
                    )
                    db.add(new_acc)
                    db.flush()
            else:
                # Cập nhật thông tin mới nhất
                sv.HoTen = str(row.get("HoTen") or row.get("Họ Tên") or sv.HoTen)
                sv.MaLop = lop_db.MaLop if lop_db else sv.MaLop

            # Lưu features
            features = RiskFeatures2(
                MSSV=mssv,
                thoi_gian_tu_hoc=float(row.get("thoi_gian_tu_hoc", 0)),
                chuyen_can=float(row.get("chuyen_can", 0)),
                diem_qua_trinh=float(row.get("diem_qua_trinh", 0)),
                hoan_thanh_bai_tap=float(row.get("hoan_thanh_bai_tap", 0)),
                tre_hoc=float(row.get("tre_hoc", 0)),
                loai_mon_hoc=str(row.get("loai_mon_hoc", "Đại cương")),
                tai_lieu_on_tap=str(row.get("tai_lieu_on_tap", "Có")),
                hinh_thuc_thi=str(row.get("hinh_thuc_thi", "Tự luận")),
                tre_hoc_phi=str(row.get("tre_hoc_phi", "Không")),
                ho_tro=str(row.get("ho_tro", "Có")),
                hoc_nhom=str(row.get("hoc_nhom", "Có")),
                lam_them=str(row.get("lam_them", "Không")),
                co_kinh_nghiem=str(row.get("co_kinh_nghiem", "Không"))
            )
            db.add(features)
            db.flush()

            # Lấy kết quả AI cho sinh viên này
            res = ai_results[idx] if idx < len(ai_results) else {}
            risk_score = _extract_risk_score(res)
            risk_level = _extract_risk_level(res)
            warning_reasons = _extract_warning_reasons(res)

            # Lưu kết quả dự báo
            pred_result = PredictionResult2(
                MSSV=mssv,
                batch_id=batch.id,
                features_id=features.id,
                risk_score=risk_score,
                risk_level=risk_level,
                warning_reasons=warning_reasons,
                ten_mon_hoc=ten_mon,
                is_repredict=False
            )
            db.add(pred_result)
            db.flush()

            # Tự động sinh lộ trình và bài tập nếu có rủi ro
            if warning_reasons:
                _auto_generate_learning_content(db, mssv, pred_result.id, warning_reasons)

        db.commit()
        return {
            "message": "Dự báo thành công!",
            "batch_id": batch.id,
            "total_students": len(df),
            "ten_dot": batch.ten_dot
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu Database: {str(e)}")


# ─────────────────────────────────────────────────────────────────
#  2. SINH VIÊN TỰ DỰ BÁO LẠI
# ─────────────────────────────────────────────────────────────────
class RepredictRequest(BaseModel):
    thoi_gian_tu_hoc: float = 0.0
    chuyen_can: float = 0.0
    diem_qua_trinh: float = 0.0
    hoan_thanh_bai_tap: float = 0.0
    tre_hoc: float = 0.0
    loai_mon_hoc: str = "Đại cương"
    tai_lieu_on_tap: str = "Có"
    hinh_thuc_thi: str = "Tự luận"
    tre_hoc_phi: str = "Không"
    ho_tro: str = "Có"
    hoc_nhom: str = "Có"
    lam_them: str = "Không"
    co_kinh_nghiem: str = "Không"
    parent_result_id: Optional[int] = None  # ID kết quả gốc để so sánh


@router.post("/repredict/{mssv}")
def student_repredict(
    mssv: str,
    data: RepredictRequest,
    db: Session = Depends(get_db_v2)
):
    """Sinh viên cập nhật thông số và dự báo lại — kết quả được lưu riêng để so sánh"""
    sv = db.query(SinhVien2).filter(SinhVien2.MSSV == mssv).first()
    if not sv:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    payload = {
        "thoi_gian_tu_hoc": data.thoi_gian_tu_hoc,
        "chuyen_can": data.chuyen_can,
        "diem_qua_trinh": data.diem_qua_trinh,
        "hoan_thanh_bai_tap": data.hoan_thanh_bai_tap,
        "tre_hoc": data.tre_hoc,
        "loai_mon_hoc": data.loai_mon_hoc,
        "tai_lieu_on_tap": data.tai_lieu_on_tap,
        "hinh_thuc_thi": data.hinh_thuc_thi,
        "tre_hoc_phi": data.tre_hoc_phi,
        "ho_tro": data.ho_tro,
        "hoc_nhom": data.hoc_nhom,
        "lam_them": data.lam_them,
        "co_kinh_nghiem": data.co_kinh_nghiem
    }

    try:
        # Gọi AI dự báo 1 sinh viên
        response = requests.post(AI_PREDICT_SINGLE_URL, json=payload, timeout=60)
        if response.status_code != 200:
            # Fallback: dùng batch endpoint với 1 phần tử
            response = requests.post(AI_PREDICT_BATCH_URL, json=[payload], timeout=60)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"AI lỗi: {response.text}")
        ai_result = response.json()
        if isinstance(ai_result, list):
            ai_result = ai_result[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối AI: {str(e)}")

    risk_score = _extract_risk_score(ai_result)
    risk_level = _extract_risk_level(ai_result)
    warning_reasons = _extract_warning_reasons(ai_result)

    try:
        # Lưu features mới
        features = RiskFeatures2(MSSV=mssv, **{k: v for k, v in payload.items()})
        db.add(features)
        db.flush()

        # Lấy ten_mon_hoc từ kết quả gốc (nếu có)
        parent_ten_mon = None
        if data.parent_result_id:
            parent_result = db.query(PredictionResult2).filter(PredictionResult2.id == data.parent_result_id).first()
            if parent_result:
                parent_ten_mon = parent_result.ten_mon_hoc

        # Lưu kết quả dự báo lại
        pred_result = PredictionResult2(
            MSSV=mssv,
            batch_id=None,
            features_id=features.id,
            risk_score=risk_score,
            risk_level=risk_level,
            warning_reasons=warning_reasons,
            ten_mon_hoc=parent_ten_mon,
            is_repredict=True,
            parent_result_id=data.parent_result_id
        )
        db.add(pred_result)
        db.flush()

        # Sinh lộ trình + bài tập mới nếu còn rủi ro
        if warning_reasons:
            _auto_generate_learning_content(db, mssv, pred_result.id, warning_reasons)

        db.commit()

        return {
            "message": "Dự báo lại thành công!",
            "result_id": pred_result.id,
            "risk_score": risk_score,
            "risk_score_percent": round(risk_score * 100, 2),
            "risk_level": risk_level,
            "warning_reasons": warning_reasons,
            "parent_result_id": data.parent_result_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu DB: {str(e)}")


# ─────────────────────────────────────────────────────────────────
#  3. HELPER FUNCTIONS — Trích xuất dữ liệu từ AI response
# ─────────────────────────────────────────────────────────────────
def _extract_risk_score(res: dict) -> float:
    """Trích điểm rủi ro từ AI response — thử nhiều key khác nhau"""
    for key in ["risk_score", "risk_score_percent", "score", "probability"]:
        if key in res:
            val = res[key]
            # Nếu phần trăm (>1) thì chia 100
            return float(val) / 100 if float(val) > 1 else float(val)
    return 0.0


def _extract_risk_level(res: dict) -> str:
    for key in ["risk_level", "level", "label", "category"]:
        if key in res:
            return str(res[key])
    score = _extract_risk_score(res)
    if score >= 0.65:
        return "CAO"
    elif score >= 0.40:
        return "TRUNG BÌNH"
    return "AN TOÀN"


def _extract_warning_reasons(res: dict) -> list:
    """Trích danh sách lý do cảnh báo"""
    for key in ["warning_reasons", "reasons", "sorted_reasons_for_ui",
                "ai_explanation_path", "risk_factors", "factors"]:
        if key in res and res[key]:
            val = res[key]
            return val if isinstance(val, list) else [val]
    return []


def _auto_generate_learning_content(db, mssv: str, pred_result_id: int, warning_reasons: list):
    """Tự động sinh lộ trình và bài tập khi có kết quả dự báo"""
    from app.models.student_risk_v2 import LearningPath2, Exercise2
    # Xóa lộ trình & bài tập cũ liên quan prediction cũ
    db.query(LearningPath2).filter(
        LearningPath2.MSSV == mssv,
        LearningPath2.prediction_result_id == pred_result_id
    ).delete()
    db.query(Exercise2).filter(
        Exercise2.MSSV == mssv,
        Exercise2.prediction_result_id == pred_result_id
    ).delete()

    # Sinh lộ trình
    paths = generate_learning_path(mssv, pred_result_id, warning_reasons)
    for p in paths:
        db.add(LearningPath2(**p))

    # Sinh bài tập
    exs = generate_exercises(mssv, pred_result_id, warning_reasons)
    for ex in exs:
        db.add(Exercise2(**ex))
