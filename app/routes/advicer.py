from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import requests
from app.database import get_db
from app.models.student_risk import Advice

router = APIRouter(prefix="/api/advice", tags=["Advice"])

ADVICE_API_URL = "https://model-support-advice.onrender.com/get-advice"

# Định nghĩa cấu trúc dữ liệu nhận từ Frontend
class AdvicePayload(BaseModel):
    risk_reasons: str

@router.post("/generate/{mssv}")
def generate_advice(mssv: str, req: AdvicePayload, db: Session = Depends(get_db)):
    # 1. KIỂM TRA DATABASE: Xem đã có lời khuyên cho MSSV này chưa
    existing_advice = db.query(Advice).filter(Advice.MSSV == mssv).first()
    
    # Nếu ĐÃ CÓ: Lấy trực tiếp từ database trả về luôn
    if existing_advice:
        return {"status": "success", "advice": existing_advice.advice_text, "source": "database"}

    # 2. NẾU CHƯA CÓ: Chuẩn bị dữ liệu gửi cho AI
    # Lấy lý do rủi ro, nếu rỗng thì dùng mặc định
    risk_reasons = req.risk_reasons.strip() if req.risk_reasons and req.risk_reasons.strip() else "Sinh viên đang có trạng thái an toàn, điểm số và chuyên cần tốt."

    # Cập nhật Payload: Gửi object duy nhất (không phải list) để khớp với API /get-advice
    payload = {
        "student_id": mssv,
        "risk_reasons": risk_reasons
    }

    try:
        # Gọi API AI Tư vấn
        response = requests.post(ADVICE_API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            ai_data = response.json()
            # Thử lấy từ 'advice' hoặc 'analysis' tùy vào thực tế API trả về
            advice_text = ai_data.get('advice') or ai_data.get('analysis')
            
            if advice_text:
                # 3. LƯU VÀO DATABASE
                new_advice = Advice(MSSV=mssv, advice_text=advice_text)
                db.add(new_advice)
                db.commit()
                return {"status": "success", "advice": advice_text, "source": "ai"}
            else:
                raise Exception("API AI không trả về dữ liệu lời khuyên hợp lệ.")
        else:
            raise Exception(f"Lỗi từ API AI (Mã lỗi: {response.status_code})")

    except Exception as e:
        # CƠ CHẾ DỰ PHÒNG (FALLBACK): Tạo lời khuyên dựa trên rủi ro nếu AI lỗi
        fallback_advice = f"**Hệ thống tự động đề xuất:** Dựa trên các yếu tố rủi ro ({risk_reasons}), Cố vấn nên có buổi làm việc riêng với học sinh {mssv} để nắm bắt tâm tư và đưa ra lộ trình hỗ trợ học tập cụ thể."
        
        return {
            "status": "warning", 
            "advice": fallback_advice, 
            "source": "fallback",
            "error_detail": str(e)
        }