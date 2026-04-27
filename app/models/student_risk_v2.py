"""
Database models mới cho student_risk_v2
- Không ảnh hưởng đến DB cũ student_risk_mgmt
- 13 thuộc tính mới từ AI API
- Hỗ trợ lộ trình học tập, bài tập, so sánh tiến bộ
"""
from sqlalchemy import (
    JSON, Column, Integer, String, Float, ForeignKey,
    TIMESTAMP, Text, Enum, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database_v2 import Base2


# ─────────────────────────── PHÒNG ĐÀO TẠO / QUẢN TRỊ ───────────────────────────

class Khoa2(Base2):
    __tablename__ = "khoa"

    MaKhoa = Column(String(20), primary_key=True)
    TenKhoa = Column(String(100))

    sinhviens = relationship("SinhVien2", back_populates="khoa")


class Lop2(Base2):
    __tablename__ = "lop"

    MaLop = Column(String(20), primary_key=True)
    TenLop = Column(String(100), nullable=False)
    MaKhoa = Column(String(20), ForeignKey("khoa.MaKhoa"))

    khoa = relationship("Khoa2", backref="lops")
    sinhviens = relationship("SinhVien2", back_populates="lop_hoc")


class MonHoc2(Base2):
    __tablename__ = "monhoc"

    MaMonHoc = Column(String(50), primary_key=True)
    TenMonHoc = Column(String(200), nullable=False)
    LoaiMonHoc = Column(String(50), nullable=True) # VD: Đại cương, Chuyên ngành
    Nganh = Column(String(100), nullable=True) # Ngành học (Áp dụng cho môn Chuyên ngành, môn Đại cương để trống)


class SinhVien2(Base2):
    __tablename__ = "sinhvien"

    MSSV = Column(String(50), primary_key=True)
    HoTen = Column(String(100))
    MaKhoa = Column(String(20), ForeignKey("khoa.MaKhoa"))
    Nganh = Column(String(100))
    MaLop = Column(String(20), ForeignKey("lop.MaLop"), nullable=True)
    Email = Column(String(150), nullable=True)
    NgaySinh = Column(String(20), nullable=True)

    khoa = relationship("Khoa2", back_populates="sinhviens")
    lop_hoc = relationship("Lop2", back_populates="sinhviens")
    account = relationship("TaiKhoan2", back_populates="sinhvien", uselist=False)
    features = relationship("RiskFeatures2", back_populates="sinhvien")
    prediction_results = relationship("PredictionResult2", back_populates="sinhvien")
    learning_paths = relationship("LearningPath2", back_populates="sinhvien")
    exercises = relationship("Exercise2", back_populates="sinhvien")


class TaiKhoan2(Base2):
    __tablename__ = "taikhoan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True)
    password = Column(String(255))
    role = Column(Enum("admin", "sinhvien"))
    MSSV_LienKet = Column(String(50), ForeignKey("sinhvien.MSSV"), nullable=True)

    sinhvien = relationship("SinhVien2", back_populates="account")


# ─────────────────────────── DỮ LIỆU ĐẶC TRƯNG (13 TRƯỜNG MỚI) ─────────────────

class RiskFeatures2(Base2):
    """
    Lưu 13 thuộc tính đầu vào cho AI — tương ứng trực tiếp với schema AIStudentData
    """
    __tablename__ = "risk_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    MSSV = Column(String(50), ForeignKey("sinhvien.MSSV"))

    # Thuộc tính số (float)
    thoi_gian_tu_hoc = Column(Float, nullable=False, default=0.0)   # giờ/tuần
    chuyen_can = Column(Float, nullable=False, default=0.0)          # % chuyên cần
    diem_qua_trinh = Column(Float, nullable=False, default=0.0)      # điểm 0-10
    hoan_thanh_bai_tap = Column(Float, nullable=False, default=0.0)  # % hoàn thành
    tre_hoc = Column(Float, nullable=False, default=0.0)             # số lần trễ

    # Thuộc tính phân loại (string)
    loai_mon_hoc = Column(String(50), nullable=False, default="Đại cương")
    tai_lieu_on_tap = Column(String(50), nullable=False, default="Có")
    hinh_thuc_thi = Column(String(50), nullable=False, default="Tự luận")
    tre_hoc_phi = Column(String(10), nullable=False, default="Không")
    ho_tro = Column(String(10), nullable=False, default="Có")
    hoc_nhom = Column(String(10), nullable=False, default="Có")
    lam_them = Column(String(10), nullable=False, default="Không")
    co_kinh_nghiem = Column(String(10), nullable=False, default="Không")

    created_at = Column(TIMESTAMP, server_default=func.now())

    sinhvien = relationship("SinhVien2", back_populates="features")


# ─────────────────────────── KẾT QUẢ DỰ BÁO ─────────────────────────────────────

class PredictionBatch2(Base2):
    """
    Lô dự báo — mỗi lần phòng đào tạo upload CSV tạo 1 batch
    """
    __tablename__ = "prediction_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ten_dot = Column(String(200), nullable=True)          # Tên đợt (vd: "Học kỳ 1 - 2024")
    mo_ta = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("taikhoan.id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    results = relationship("PredictionResult2", back_populates="batch")


class PredictionResult2(Base2):
    """
    Kết quả dự báo từng sinh viên trong 1 batch
    """
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    MSSV = Column(String(50), ForeignKey("sinhvien.MSSV"))
    batch_id = Column(Integer, ForeignKey("prediction_batches.id"), nullable=True)
    features_id = Column(Integer, ForeignKey("risk_features.id"), nullable=True)

    # Kết quả từ AI
    risk_score = Column(Float, nullable=False, default=0.0)   # 0.0 - 1.0
    risk_level = Column(String(50), nullable=False, default="AN TOÀN")
    warning_reasons = Column(JSON, nullable=True)   # list các reason keys từ AI

    is_repredict = Column(Boolean, default=False)   # True nếu là dự báo lại của sinh viên
    parent_result_id = Column(Integer, ForeignKey("prediction_results.id"), nullable=True)  # ID kết quả gốc

    created_at = Column(TIMESTAMP, server_default=func.now())

    sinhvien = relationship("SinhVien2", back_populates="prediction_results")
    batch = relationship("PredictionBatch2", back_populates="results")


# ─────────────────────────── LỘ TRÌNH HỌC TẬP ───────────────────────────────────

class LearningPath2(Base2):
    """
    Lộ trình học tập được tạo tự động dựa trên warning_reasons
    """
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, autoincrement=True)
    MSSV = Column(String(50), ForeignKey("sinhvien.MSSV"))
    prediction_result_id = Column(Integer, ForeignKey("prediction_results.id"), nullable=True)

    risk_reason_key = Column(String(100))    # key rủi ro (vd: "chuyen_can")
    risk_reason_label = Column(String(200))  # nhãn hiển thị (vd: "Chuyên cần thấp")
    muc_tieu = Column(Text)                  # Mục tiêu cần đạt
    hanh_dong = Column(JSON)                 # List các hành động cụ thể
    status = Column(Enum("todo", "in_progress", "done"), default="todo")

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    sinhvien = relationship("SinhVien2", back_populates="learning_paths")


# ─────────────────────────── BÀI TẬP & TEST ──────────────────────────────────────

class Exercise2(Base2):
    """
    Bài tập trắc nghiệm sinh ra theo từng rủi ro
    """
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    MSSV = Column(String(50), ForeignKey("sinhvien.MSSV"))
    prediction_result_id = Column(Integer, ForeignKey("prediction_results.id"), nullable=True)

    risk_reason_key = Column(String(100))    # key rủi ro liên quan
    risk_reason_label = Column(String(200))
    question = Column(Text)                  # Câu hỏi
    options = Column(JSON)                   # List 4 đáp án
    correct_index = Column(Integer)          # Index đáp án đúng (0-3)
    explanation = Column(Text)               # Giải thích đáp án

    created_at = Column(TIMESTAMP, server_default=func.now())

    sinhvien = relationship("SinhVien2", back_populates="exercises")
    results = relationship("ExerciseResult2", back_populates="exercise")


class ExerciseResult2(Base2):
    """
    Kết quả làm bài của sinh viên
    """
    __tablename__ = "exercise_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    MSSV = Column(String(50), ForeignKey("sinhvien.MSSV"))
    chosen_index = Column(Integer)           # Đáp án sinh viên chọn
    is_correct = Column(Boolean, default=False)
    completed_at = Column(TIMESTAMP, server_default=func.now())

    exercise = relationship("Exercise2", back_populates="results")

class CauHoiTamLy2(Base2):
    """
    Ngân hàng 300 câu hỏi tâm lý/thói quen học tập
    """
    __tablename__ = "cau_hoi_tam_ly"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thuoc_tinh = Column(String(50), index=True) # VD: chuyen_can, ap_luc...
    cau_hoi = Column(Text, nullable=False)
    options = Column(JSON, nullable=False) # List ["A. ...", "B. ...", "C. ...", "D. ..."]
    correct_index = Column(Integer, nullable=False) # 0, 1, 2, 3
    diem_so = Column(Integer, default=1)
    giai_thich = Column(Text, nullable=True)


class LichSuTestTamLy2(Base2):
    """
    Lưu vết các câu hỏi sinh viên đã làm để tránh random lặp lại
    """
    __tablename__ = "lich_su_test_tam_ly"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mssv = Column(String(50), ForeignKey("sinhvien.MSSV"), index=True)
    cau_hoi_id = Column(Integer, ForeignKey("cau_hoi_tam_ly.id"))
    chosen_index = Column(Integer)
    is_correct = Column(Boolean)
    ngay_lam = Column(TIMESTAMP, server_default=func.now())

    cau_hoi_rel = relationship("CauHoiTamLy2")
