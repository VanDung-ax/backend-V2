"""
main_v2.py — FastAPI app dùng database student_risk_v2
Chạy: uvicorn main_v2:app --reload --port 8001

Không ảnh hưởng đến main.py cũ (database student_risk_mgmt)
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import tất cả models v2 để SQLAlchemy nhận biết trước khi create_all
from app.models import student_risk_v2  # noqa: F401

from app.database_v2 import engine_v2, Base2, get_db_v2
from app.routes import (
    authr_v2, studentr_v2, predict_v2, history_v2, learningr, accountr_v2
)

# Tự động tạo tất cả bảng trong student_risk_v2 (nếu chưa có)
Base2.metadata.create_all(bind=engine_v2)

app = FastAPI(
    title="Hệ thống Cảnh báo Học tập Sớm — V2",
    description="API dành cho Phòng Đào Tạo và Sinh Viên (database: student_risk_v2)",
    version="2.0.0"
)

# CORS — cho phép React frontend gọi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routers V2
app.include_router(authr_v2.router)
app.include_router(accountr_v2.router)
app.include_router(studentr_v2.router)
app.include_router(predict_v2.router)
app.include_router(history_v2.router)
app.include_router(learningr.router)


@app.get("/")
def root():
    return {
        "message": "Backend V2 đang chạy ổn định!",
        "database": "student_risk_v2",
        "version": "2.0.0"
    }


@app.get("/healthcheck")
def healthcheck(db: Session = Depends(get_db_v2)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "message": "Hệ thống V2 và Database đang hoạt động!",
            "database": "student_risk_v2 — connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Không thể kết nối Database V2",
            "error": str(e)
        }
