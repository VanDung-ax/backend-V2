"""
Auth routes — database student_risk_v2 (chỉ admin và sinhvien)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib
from app.database_v2 import get_db_v2
from app.models.student_risk_v2 import TaiKhoan2, SinhVien2

router = APIRouter(prefix="/api/v2/auth", tags=["Authentication V2"])

def verify_password(plain_password: str, db_password: str) -> bool:
    # Nếu password trong DB là hash SHA-256 (64 ký tự)
    if len(db_password) == 64:
        hashed = hashlib.sha256(plain_password.encode()).hexdigest()
        return hashed == db_password
    # Nếu là plaintext (VD: admin123)
    return plain_password == db_password


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db_v2)):
    user = db.query(TaiKhoan2).filter(TaiKhoan2.username == request.username).first()

    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác")

    linked_id = None
    display_name = user.username

    if user.role == "sinhvien" and user.sinhvien:
        display_name = user.sinhvien.HoTen
        linked_id = user.MSSV_LienKet
    elif user.role == "admin":
        display_name = "Phòng Đào Tạo"

    return {
        "status": "success",
        "message": "Đăng nhập thành công",
        "id": user.id,
        "role": user.role,
        "username": user.username,
        "display_name": display_name,
        "linked_id": linked_id
    }


@router.post("/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db_v2)):
    user = db.query(TaiKhoan2).filter(TaiKhoan2.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    if not verify_password(request.old_password, user.password):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
    
    # Mã hóa mật khẩu mới trước khi lưu
    user.password = hashlib.sha256(request.new_password.encode()).hexdigest()
    db.commit()
    return {"status": "success", "message": "Đổi mật khẩu thành công"}
