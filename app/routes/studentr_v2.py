"""
Routes quản lý sinh viên — database student_risk_v2
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database_v2 import get_db_v2
from app.models.student_risk_v2 import (
    SinhVien2, Khoa2, TaiKhoan2, RiskFeatures2, PredictionResult2,
    LearningPath2, Exercise2, ExerciseResult2
)
import hashlib

router = APIRouter(prefix="/api/v2/student", tags=["Quản lý Sinh viên V2"])


class StudentCreate(BaseModel):
    MSSV: str
    HoTen: str
    MaKhoa: str
    Nganh: str
    Lop: Optional[str] = None
    Email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class StudentInfoResponse(BaseModel):
    MSSV: str
    HoTen: str
    MaKhoa: str
    TenKhoa: Optional[str] = None
    Nganh: str

    class Config:
        from_attributes = True


@router.get("/all")
def get_all_students(db: Session = Depends(get_db_v2)):
    students = db.query(SinhVien2).filter(SinhVien2.MSSV.isnot(None)).all()
    return [{
        "MSSV": s.MSSV,
        "HoTen": s.HoTen or "Chưa có tên",
        "MaKhoa": s.MaKhoa or "Chưa xác định",
        "TenKhoa": s.khoa.TenKhoa if s.khoa else "Chưa xác định",
        "Nganh": s.Nganh or "Chưa xác định",
        "MaLop": s.MaLop or "",
        "Email": s.Email or ""
    } for s in students]


@router.post("/add")
def add_student(data: StudentCreate, db: Session = Depends(get_db_v2)):
    if db.query(SinhVien2).filter(SinhVien2.MSSV == data.MSSV).first():
        raise HTTPException(status_code=400, detail="MSSV đã tồn tại!")

    username = data.username or data.MSSV
    if db.query(TaiKhoan2).filter(TaiKhoan2.username == username).first():
        raise HTTPException(status_code=400, detail=f"Tài khoản '{username}' đã tồn tại!")

    try:
        # Đảm bảo khoa tồn tại
        khoa = db.query(Khoa2).filter(Khoa2.MaKhoa == data.MaKhoa).first()
        if not khoa:
            khoa = Khoa2(MaKhoa=data.MaKhoa[:20], TenKhoa=data.MaKhoa)
            db.add(khoa)
            db.flush()

        new_sv = SinhVien2(
            MSSV=data.MSSV,
            HoTen=data.HoTen,
            MaKhoa=data.MaKhoa,
            Nganh=data.Nganh,
            MaLop=data.Lop,
            Email=data.Email
        )
        db.add(new_sv)
        db.flush()

        # Tạo tài khoản mặc định
        raw_password = data.password or "1234"
        hashed = hashlib.sha256(raw_password.encode()).hexdigest()
        account = TaiKhoan2(
            username=username,
            password=hashed,
            role="sinhvien",
            MSSV_LienKet=data.MSSV
        )
        db.add(account)
        db.commit()
        return {"status": "success", "message": f"Đã thêm sinh viên {data.MSSV}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi DB: {str(e)}")


@router.delete("/delete/{mssv}")
def delete_student(mssv: str, db: Session = Depends(get_db_v2)):
    sv = db.query(SinhVien2).filter(SinhVien2.MSSV == mssv).first()
    if not sv:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    # Xóa theo thứ tự để tránh FK constraint
    db.query(ExerciseResult2).filter(ExerciseResult2.MSSV == mssv).delete()
    db.query(Exercise2).filter(Exercise2.MSSV == mssv).delete()
    db.query(LearningPath2).filter(LearningPath2.MSSV == mssv).delete()
    db.query(PredictionResult2).filter(PredictionResult2.MSSV == mssv).delete()
    db.query(RiskFeatures2).filter(RiskFeatures2.MSSV == mssv).delete()
    db.query(TaiKhoan2).filter(TaiKhoan2.MSSV_LienKet == mssv).delete()
    db.delete(sv)
    db.commit()
    return {"status": "success"}


@router.get("/{identifier}")
def get_student_info(identifier: str, db: Session = Depends(get_db_v2)):
    sv = db.query(SinhVien2).filter(SinhVien2.MSSV == identifier).first()
    if not sv:
        account = db.query(TaiKhoan2).filter(TaiKhoan2.username == identifier).first()
        if account and account.MSSV_LienKet:
            sv = db.query(SinhVien2).filter(SinhVien2.MSSV == account.MSSV_LienKet).first()
    if not sv:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    return {
        "MSSV": sv.MSSV,
        "HoTen": sv.HoTen,
        "Nganh": sv.Nganh,
        "MaKhoa": sv.MaKhoa,
        "TenKhoa": sv.khoa.TenKhoa if sv.khoa else "Chưa cập nhật",
        "MaLop": sv.MaLop or "",
        "Email": sv.Email or ""
    }
