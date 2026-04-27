"""
Kết nối database MỚI: student_risk_v2
Hoàn toàn độc lập với database.py cũ (student_risk_mgmt)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database MỚI — student_risk_v2
# Mặc định local: mysql+mysqlconnector://root:root@localhost:3306/student_risk_v2
SQLALCHEMY_DATABASE_URL_V2 = os.getenv(
    "DATABASE_URL_V2",
    "mysql+mysqlconnector://root:root@localhost:3306/student_risk_v2"
)

engine_v2 = create_engine(SQLALCHEMY_DATABASE_URL_V2)
SessionLocalV2 = sessionmaker(autocommit=False, autoflush=False, bind=engine_v2)

Base2 = declarative_base()


def get_db_v2():
    db = SessionLocalV2()
    try:
        yield db
    finally:
        db.close()
