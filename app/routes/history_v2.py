"""
Routes data lịch sử & dashboard — database student_risk_v2
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import json

from app.database_v2 import get_db_v2
from app.models.student_risk_v2 import (
    SinhVien2, TaiKhoan2, Khoa2, Lop2,
    RiskFeatures2, PredictionBatch2, PredictionResult2
)

router = APIRouter(prefix="/api/v2", tags=["Dashboard & Lịch sử"])


@router.get("/data/all-results")
def get_all_results(
    user_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    db: Session = Depends(get_db_v2)
):
    """
    Lấy kết quả dự báo mới nhất của tất cả sinh viên
    (hoặc lọc theo batch_id)
    """
    # Subquery: lấy prediction_result.id mới nhất cho mỗi MSSV
    # Nếu có batch_id thì chỉ lấy trong batch đó
    subquery_filter = [PredictionResult2.is_repredict == False]
    if batch_id and batch_id != "all":
        try:
            bid = int(batch_id)
            subquery_filter.append(PredictionResult2.batch_id == bid)
        except:
            pass

    latest_ids_sq = (
        db.query(
            PredictionResult2.MSSV,
            func.max(PredictionResult2.id).label("max_id")
        )
        .filter(*subquery_filter)
        .group_by(PredictionResult2.MSSV)
        .subquery()
    )

    query = (
        db.query(SinhVien2, PredictionResult2, RiskFeatures2, PredictionBatch2, Khoa2)
        .outerjoin(
            latest_ids_sq,
            SinhVien2.MSSV == latest_ids_sq.c.MSSV
        )
        .outerjoin(
            PredictionResult2,
            PredictionResult2.id == latest_ids_sq.c.max_id
        )
        .outerjoin(RiskFeatures2, PredictionResult2.features_id == RiskFeatures2.id)
        .outerjoin(PredictionBatch2, PredictionResult2.batch_id == PredictionBatch2.id)
        .outerjoin(Khoa2, SinhVien2.MaKhoa == Khoa2.MaKhoa)
    )

    # Nếu lọc theo batch_id thì chỉ hiện những sinh viên CÓ kết quả trong batch đó
    if batch_id and batch_id != "all":
        query = query.filter(latest_ids_sq.c.max_id != None)

    results = query.all()
    print(f"DEBUG: get_all_results called with batch_id={batch_id}. Total rows found: {len(results)}")
    result_list = []
    for sv, pred, features, batch, khoa in results:
        result_list.append({
            "MSSV": sv.MSSV,
            "HoTen": sv.HoTen,
            "Khoa": sv.MaKhoa,
            "TenKhoa": khoa.TenKhoa if khoa else sv.MaKhoa,
            "Lop": sv.MaLop or "Chưa xếp lớp",
            "Nganh": sv.Nganh or "",
            "risk_score": pred.risk_score if pred else 0.0,
            "risk_score_percent": round((pred.risk_score or 0) * 100, 2) if pred else 0.0,
            "risk_level": pred.risk_level if pred else "AN TOÀN",
            "warning_reasons": pred.warning_reasons if pred else [],
            "result_id": pred.id if pred else None,
            "batch_id": batch.id if batch else None,
            "ten_dot": batch.ten_dot if batch else None,
            "created_at": batch.created_at.isoformat() if batch and batch.created_at else None,
            # 13 features
            "thoi_gian_tu_hoc": features.thoi_gian_tu_hoc if features else 0,
            "chuyen_can": features.chuyen_can if features else 0,
            "diem_qua_trinh": features.diem_qua_trinh if features else 0,
            "hoan_thanh_bai_tap": features.hoan_thanh_bai_tap if features else 0,
            "tre_hoc": features.tre_hoc if features else 0,
            "loai_mon_hoc": features.loai_mon_hoc if features else "",
            "tai_lieu_on_tap": features.tai_lieu_on_tap if features else "",
            "hinh_thuc_thi": features.hinh_thuc_thi if features else "",
            "tre_hoc_phi": features.tre_hoc_phi if features else "",
            "ho_tro": features.ho_tro if features else "",
            "hoc_nhom": features.hoc_nhom if features else "",
            "lam_them": features.lam_them if features else "",
            "co_kinh_nghiem": features.co_kinh_nghiem if features else ""
        })

    return result_list


@router.get("/data/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db_v2)):
    """Thống kê tổng quan cho Phòng Đào Tạo"""
    total_sv = db.query(func.count(SinhVien2.MSSV)).scalar()
    total_batches = db.query(func.count(PredictionBatch2.id)).scalar()

    # Số sinh viên có rủi ro cao (>= 0.65) trong dự báo gần nhất
    latest_ids_sq = (
        db.query(
            PredictionResult2.MSSV,
            func.max(PredictionResult2.id).label("max_id")
        )
        .filter(PredictionResult2.is_repredict == False)
        .group_by(PredictionResult2.MSSV)
        .subquery()
    )
    high_risk_count = (
        db.query(func.count(PredictionResult2.id))
        .join(latest_ids_sq, PredictionResult2.id == latest_ids_sq.c.max_id)
        .filter(PredictionResult2.risk_score >= 0.65)
        .scalar()
    )
    medium_risk_count = (
        db.query(func.count(PredictionResult2.id))
        .join(latest_ids_sq, PredictionResult2.id == latest_ids_sq.c.max_id)
        .filter(PredictionResult2.risk_score >= 0.40, PredictionResult2.risk_score < 0.65)
        .scalar()
    )

    return {
        "total_sinhvien": total_sv,
        "total_batches": total_batches,
        "high_risk_count": high_risk_count,
        "medium_risk_count": medium_risk_count,
        "safe_count": total_sv - high_risk_count - medium_risk_count
    }


@router.get("/data/batches")
def get_batches(db: Session = Depends(get_db_v2)):
    """Lấy danh sách tất cả lô dự báo"""
    batches = db.query(PredictionBatch2).order_by(PredictionBatch2.created_at.desc()).all()
    result = []
    for b in batches:
        count = db.query(func.count(PredictionResult2.id)).filter(
            PredictionResult2.batch_id == b.id,
            PredictionResult2.is_repredict == False
        ).scalar()
        result.append({
            "id": b.id,
            "ten_dot": b.ten_dot,
            "mo_ta": b.mo_ta,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "student_count": count
        })
    return result
