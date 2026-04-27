"""
Account management routes — database student_risk_v2
Chỉ có 2 role: admin, sinhvien
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database_v2 import get_db_v2
from app.models.student_risk_v2 import TaiKhoan2

router = APIRouter(prefix="/api/v2/account", tags=["Quản lý Tài khoản V2"])


class AccountCreate(BaseModel):
    username: str
    password: str
    role: str  # "admin" hoặc "sinhvien"
    MSSV_LienKet: Optional[str] = None


class AccountUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    MSSV_LienKet: Optional[str] = None


@router.get("/all")
def get_all_accounts(db: Session = Depends(get_db_v2)):
    accounts = db.query(TaiKhoan2).all()
    return [{
        "id": a.id,
        "username": a.username,
        "role": a.role,
        "MSSV_LienKet": a.MSSV_LienKet
    } for a in accounts]


@router.post("/add")
def add_account(acc: AccountCreate, db: Session = Depends(get_db_v2)):
    if acc.role not in ["admin", "sinhvien"]:
        raise HTTPException(status_code=400, detail="Role phải là 'admin' hoặc 'sinhvien'")
    if db.query(TaiKhoan2).filter(TaiKhoan2.username == acc.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    import hashlib
    hashed_password = hashlib.sha256(acc.password.encode()).hexdigest()

    new_acc = TaiKhoan2(
        username=acc.username,
        password=hashed_password,
        role=acc.role,
        MSSV_LienKet=acc.MSSV_LienKet
    )
    db.add(new_acc)
    try:
        db.commit()
        db.refresh(new_acc)
        return {"status": "success", "id": new_acc.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update/{account_id}")
def update_account(account_id: int, acc: AccountUpdate, db: Session = Depends(get_db_v2)):
    db_acc = db.query(TaiKhoan2).filter(TaiKhoan2.id == account_id).first()
    if not db_acc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    if acc.role:
        db_acc.role = acc.role
    if acc.MSSV_LienKet is not None:
        db_acc.MSSV_LienKet = acc.MSSV_LienKet
    if acc.password:
        import hashlib
        db_acc.password = hashlib.sha256(acc.password.encode()).hexdigest()
    try:
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db_v2)):
    db_acc = db.query(TaiKhoan2).filter(TaiKhoan2.id == account_id).first()
    if not db_acc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    db.delete(db_acc)
    try:
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
