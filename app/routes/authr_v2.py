"""
Auth routes — database student_risk_v2 (chỉ admin và sinhvien)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib
import bcrypt
from app.database_v2 import get_db_v2
from app.models.student_risk_v2 import TaiKhoan2, SinhVien2

router = APIRouter(prefix="/api/v2/auth", tags=["Authentication V2"])

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, db_password: str) -> bool:
    # 1. Kiểm tra chuẩn Bcrypt (bắt đầu bằng $2b$ hoặc $2a$)
    if db_password.startswith("$2b$") or db_password.startswith("$2a$"):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), db_password.encode('utf-8'))
        except ValueError:
            return False
            
    # 2. Hỗ trợ tài khoản cũ (SHA-256)
    if len(db_password) == 64:
        hashed = hashlib.sha256(plain_password.encode()).hexdigest()
        return hashed == db_password
        
    # 3. Hỗ trợ tài khoản cực cũ (Plaintext)
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

    # AUTO-UPGRADE: Nếu mật khẩu trong DB chưa chuẩn Bcrypt, nâng cấp ngay
    if not (user.password.startswith("$2b$") or user.password.startswith("$2a$")):
        user.password = hash_password(request.password)
        db.commit()

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
    
    # Mã hóa mật khẩu mới bằng Bcrypt
    user.password = hash_password(request.new_password)
    db.commit()
    return {"status": "success", "message": "Đổi mật khẩu thành công"}
