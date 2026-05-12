"""
Routes: Lộ trình học tập & Bài tập trắc nghiệm
Database: student_risk_v2
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import requests

from app.database_v2 import get_db_v2
from app.models.student_risk_v2 import (
    SinhVien2, LearningPath2, Exercise2, ExerciseResult2, PredictionResult2,
    CauHoiTamLy2, LichSuTestTamLy2, AIRoadmap2
)
from app.services.learning_engine import generate_learning_path, generate_exercises

router = APIRouter(prefix="/api/v2", tags=["Lộ trình & Bài tập"])


from app.models.student_risk_v2 import MonHoc2

# ─────────────────────────────────────────────────────────────────
#  DANH SÁCH MÔN HỌC
# ─────────────────────────────────────────────────────────────────
@router.get("/monhoc")
def get_all_monhoc(db: Session = Depends(get_db_v2)):
    monhocs = db.query(MonHoc2).all()
    return [{"MaMonHoc": m.MaMonHoc, "TenMonHoc": m.TenMonHoc} for m in monhocs]


# ─────────────────────────────────────────────────────────────────
#  LỘ TRÌNH HỌC TẬP
# ─────────────────────────────────────────────────────────────────

@router.get("/learning-path/{mssv}")
def get_learning_path(mssv: str, db: Session = Depends(get_db_v2)):
    """Lấy lộ trình học tập của sinh viên từ kết quả dự báo gần nhất"""
    # Lấy kết quả dự báo gần nhất
    latest_result = (
        db.query(PredictionResult2)
        .filter(PredictionResult2.MSSV == mssv)
        .order_by(PredictionResult2.created_at.desc())
        .first()
    )
    if not latest_result:
        return {"paths": [], "message": "Chưa có kết quả dự báo"}

    # Tự sinh mới nếu chưa có
    existing = db.query(LearningPath2).filter(
        LearningPath2.MSSV == mssv,
        LearningPath2.prediction_result_id == latest_result.id
    ).all()

    if not existing and latest_result.warning_reasons:
        paths_data = generate_learning_path(mssv, latest_result.id, latest_result.warning_reasons)
        for p in paths_data:
            db.add(LearningPath2(**p))
        db.commit()
        existing = db.query(LearningPath2).filter(
            LearningPath2.MSSV == mssv,
            LearningPath2.prediction_result_id == latest_result.id
        ).all()

    return {
        "paths": [
            {
                "id": p.id,
                "risk_reason_key": p.risk_reason_key,
                "risk_reason_label": p.risk_reason_label,
                "muc_tieu": p.muc_tieu,
                "hanh_dong": p.hanh_dong,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in existing
        ],
        "total": len(existing),
        "done_count": sum(1 for p in existing if p.status == "done"),
        "result_id": latest_result.id,
        "risk_score": latest_result.risk_score,
        "risk_level": latest_result.risk_level
    }


@router.put("/learning-path/{path_id}/status")
def update_path_status(
    path_id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db_v2)
):
    """Cập nhật trạng thái task lộ trình (todo / in_progress / done)"""
    if status not in ["todo", "in_progress", "done"]:
        raise HTTPException(status_code=400, detail="Status không hợp lệ")
    path = db.query(LearningPath2).filter(LearningPath2.id == path_id).first()
    if not path:
        raise HTTPException(status_code=404, detail="Không tìm thấy lộ trình")
    path.status = status
    db.commit()
    return {"message": "Cập nhật thành công", "status": status}


# ─────────────────────────────────────────────────────────────────
#  BÀI TẬP & TEST
# ─────────────────────────────────────────────────────────────────

@router.get("/exercises/{mssv}")
def get_exercises(mssv: str, db: Session = Depends(get_db_v2)):
    """Lấy danh sách bài tập của sinh viên từ kết quả dự báo gần nhất"""
    latest_result = (
        db.query(PredictionResult2)
        .filter(PredictionResult2.MSSV == mssv)
        .order_by(PredictionResult2.created_at.desc())
        .first()
    )
    if not latest_result:
        return {"exercises": [], "message": "Chưa có kết quả dự báo"}

    # Tự sinh mới nếu chưa có
    existing = db.query(Exercise2).filter(
        Exercise2.MSSV == mssv,
        Exercise2.prediction_result_id == latest_result.id
    ).all()

    if not existing and latest_result.warning_reasons:
        exs_data = generate_exercises(mssv, latest_result.id, latest_result.warning_reasons)
        for ex in exs_data:
            db.add(Exercise2(**ex))
        db.commit()
        existing = db.query(Exercise2).filter(
            Exercise2.MSSV == mssv,
            Exercise2.prediction_result_id == latest_result.id
        ).all()

    # Lấy kết quả đã làm
    ex_ids = [e.id for e in existing]
    done_results = {}
    if ex_ids:
        results = db.query(ExerciseResult2).filter(
            ExerciseResult2.exercise_id.in_(ex_ids),
            ExerciseResult2.MSSV == mssv
        ).all()
        for r in results:
            done_results[r.exercise_id] = {
                "chosen_index": r.chosen_index,
                "is_correct": r.is_correct,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }

    # Group theo risk_reason
    grouped = {}
    for ex in existing:
        key = ex.risk_reason_key
        if key not in grouped:
            grouped[key] = {
                "risk_reason_key": key,
                "risk_reason_label": ex.risk_reason_label,
                "questions": []
            }
        q_data = {
            "id": ex.id,
            "question": ex.question,
            "options": ex.options,
            "explanation": ex.explanation,
            "user_result": done_results.get(ex.id)
        }
        # Chỉ tiết lộ đáp án đúng nếu sinh viên đã làm
        if ex.id in done_results:
            q_data["correct_index"] = ex.correct_index
        grouped[key]["questions"].append(q_data)

    total_questions = len(existing)
    done_count = len(done_results)
    correct_count = sum(1 for r in done_results.values() if r["is_correct"])

    return {
        "exercise_groups": list(grouped.values()),
        "total_questions": total_questions,
        "done_count": done_count,
        "correct_count": correct_count,
        "score_percent": round(correct_count / total_questions * 100, 1) if total_questions > 0 else 0,
        "result_id": latest_result.id
    }


class SubmitAnswerRequest(BaseModel):
    exercise_id: int
    mssv: str
    chosen_index: int


@router.post("/exercises/submit")
def submit_answer(data: SubmitAnswerRequest, db: Session = Depends(get_db_v2)):
    """Nộp đáp án cho 1 câu hỏi"""
    ex = db.query(Exercise2).filter(Exercise2.id == data.exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    is_correct = data.chosen_index == ex.correct_index

    # Xóa kết quả cũ nếu có (cho phép làm lại)
    db.query(ExerciseResult2).filter(
        ExerciseResult2.exercise_id == data.exercise_id,
        ExerciseResult2.MSSV == data.mssv
    ).delete()

    result = ExerciseResult2(
        exercise_id=data.exercise_id,
        MSSV=data.mssv,
        chosen_index=data.chosen_index,
        is_correct=is_correct
    )
    db.add(result)
    db.commit()

    return {
        "is_correct": is_correct,
        "correct_index": ex.correct_index,
        "explanation": ex.explanation,
        "chosen_index": data.chosen_index
    }


@router.get("/exercises/history/{mssv}")
def get_exercise_history(mssv: str, db: Session = Depends(get_db_v2)):
    """Lấy lịch sử điểm bài tập AI theo từng đợt làm bài để vẽ biểu đồ"""
    results = (
        db.query(ExerciseResult2)
        .filter(ExerciseResult2.MSSV == mssv)
        .order_by(ExerciseResult2.completed_at.asc())
        .all()
    )
    
    if not results:
        return {"history": []}
        
    from datetime import timedelta
    sessions = []
    current_session = None
    
    for r in results:
        if not r.completed_at:
            continue
            
        # Tách đợt làm bài mới nếu khoảng cách thời gian nộp bài > 2 phút
        if current_session is None or (r.completed_at - current_session["last_time"]) > timedelta(minutes=2):
            if current_session:
                sessions.append(current_session)
                
            current_session = {
                "start_time": r.completed_at,
                "last_time": r.completed_at,
                "total": 0,
                "correct": 0
            }
            
        current_session["last_time"] = r.completed_at
        current_session["total"] += 1
        if r.is_correct:
            current_session["correct"] += 1
            
    if current_session:
        sessions.append(current_session)
            
    history = []
    for i, s in enumerate(sessions):
        score = round((s["correct"] / s["total"]) * 100, 1) if s["total"] > 0 else 0
        date_str = s["start_time"].strftime("%d/%m")
        history.append({
            "name": f"{date_str} (Lần {i+1})",
            "score": score
        })
        
    return {"history": history}



# ─────────────────────────────────────────────────────────────────
#  TIẾN BỘ & SO SÁNH
# ─────────────────────────────────────────────────────────────────

@router.get("/progress/{mssv}")
def get_progress(mssv: str, db: Session = Depends(get_db_v2)):
    """Lấy toàn bộ lịch sử dự báo của sinh viên để so sánh tiến bộ"""
    results = (
        db.query(PredictionResult2)
        .filter(PredictionResult2.MSSV == mssv)
        .order_by(PredictionResult2.created_at.asc())
        .all()
    )

    if not results:
        return {"history": [], "message": "Chưa có dữ liệu dự báo"}

    from app.models.student_risk_v2 import RiskFeatures2
    history = []
    for r in results:
        # Lấy features tương ứng
        features = None
        if r.features_id:
            features = db.query(RiskFeatures2).filter(RiskFeatures2.id == r.features_id).first()

        history.append({
            "result_id": r.id,
            "batch_id": r.batch_id,
            "is_repredict": r.is_repredict,
            "parent_result_id": r.parent_result_id,
            "risk_score": r.risk_score,
            "risk_score_percent": round(r.risk_score * 100, 2),
            "risk_level": r.risk_level,
            "warning_reasons": r.warning_reasons or [],
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "features": {
                "thoi_gian_tu_hoc": features.thoi_gian_tu_hoc if features else None,
                "chuyen_can": features.chuyen_can if features else None,
                "diem_qua_trinh": features.diem_qua_trinh if features else None,
                "hoan_thanh_bai_tap": features.hoan_thanh_bai_tap if features else None,
                "tre_hoc": features.tre_hoc if features else None,
                "loai_mon_hoc": features.loai_mon_hoc if features else None,
                "tai_lieu_on_tap": features.tai_lieu_on_tap if features else None,
                "hinh_thuc_thi": features.hinh_thuc_thi if features else None,
                "tre_hoc_phi": features.tre_hoc_phi if features else None,
                "ho_tro": features.ho_tro if features else None,
                "hoc_nhom": features.hoc_nhom if features else None,
                "lam_them": features.lam_them if features else None,
                "co_kinh_nghiem": features.co_kinh_nghiem if features else None,
            } if features else None,
            "ten_mon_hoc": r.ten_mon_hoc
        })

    # Tính toán tiến bộ
    improvement = None
    if len(results) >= 2:
        first = results[0]
        last = results[-1]
        delta = first.risk_score - last.risk_score  # dương = tiến bộ
        improvement = {
            "first_score": round(first.risk_score * 100, 2),
            "last_score": round(last.risk_score * 100, 2),
            "delta_percent": round(delta * 100, 2),
            "is_improved": delta > 0,
            "sessions_count": len(results)
        }

    return {
        "history": history,
        "improvement": improvement,
        "total_sessions": len(results)
    }


# ─────────────────────────────────────────────────────────────────
#  AI QUIZ GENERATOR PROXY
# ─────────────────────────────────────────────────────────────────

class AIQuizRequest(BaseModel):
    mssv: str
    mon_hoc: str
    ly_do: str

@router.post("/generate-ai-quiz")
def generate_ai_quiz(data: AIQuizRequest, db: Session = Depends(get_db_v2)):
    """Gọi tới API AI bên ngoài để tạo bài tập"""
    url = "https://groq-advice-model.onrender.com/generate-quiz"
    payload = {
        "mssv": data.mssv,
        "mon_hoc": data.mon_hoc,
        "ly_do": data.ly_do
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result_data = response.json()
        
        # Đảm bảo result_data là dict (đôi khi AI trả về chuỗi JSON)
        import json
        if isinstance(result_data, str):
            try:
                result_data = json.loads(result_data)
            except Exception:
                pass

        # Lưu vào bảng bài tập
        latest_result = db.query(PredictionResult2).filter(PredictionResult2.MSSV == data.mssv).order_by(PredictionResult2.created_at.desc()).first()
        pred_id = latest_result.id if latest_result else None
        
        if isinstance(result_data, dict) and "danh_sach_cau_hoi" in result_data:
            for q in result_data["danh_sach_cau_hoi"]:
                options_list = list(q["dap_an"].values()) if isinstance(q.get("dap_an"), dict) else []
                correct_idx = 0
                if options_list and q.get("lua_chon_dung") in options_list:
                    correct_idx = options_list.index(q["lua_chon_dung"])
                
                ex = Exercise2(
                    MSSV=data.mssv,
                    prediction_result_id=pred_id,
                    risk_reason_key="ai_custom",
                    risk_reason_label=data.ly_do,
                    question=q.get("cau_hoi", ""),
                    options=options_list,
                    correct_index=correct_idx,
                    explanation=q.get("giai_thich", "")
                )
                db.add(ex)
                db.flush()  # Lưu tạm để lấy ID
                q["id"] = ex.id  # Trả ID về cho frontend

            db.commit()
            
        return result_data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI API: {str(e)}")

# ─────────────────────────────────────────────────────────────────
#  AI ROADMAP GENERATOR PROXY
# ─────────────────────────────────────────────────────────────────

class AIRoadmapRequest(BaseModel):
    mssv: str
    nganh: str
    mon: str
    ly_do_rot: str

@router.get("/ai-roadmap/{mssv}")
def get_ai_roadmap(mssv: str, db: Session = Depends(get_db_v2)):
    """Lấy lộ trình AI đã tạo gần nhất của sinh viên"""
    roadmap = db.query(AIRoadmap2).filter(AIRoadmap2.MSSV == mssv).order_by(AIRoadmap2.created_at.desc()).first()
    if not roadmap:
        return None
    return {
        "mssv": roadmap.MSSV,
        "mon_hoc": roadmap.mon_hoc,
        "ly_do_rot": roadmap.ly_do_rot,
        "loi_khuyen": roadmap.loi_khuyen,
        "tuan_1": roadmap.tuan_1,
        "tuan_2": roadmap.tuan_2
    }

@router.post("/generate-ai-roadmap")
def generate_ai_roadmap(data: AIRoadmapRequest, db: Session = Depends(get_db_v2)):
    """Gọi tới API AI bên ngoài để tạo lộ trình và lưu vào DB"""
    url = "https://advice-student-model.onrender.com/consult"
    
    mssv_val = int(data.mssv) if data.mssv.isdigit() else data.mssv
    payload = {
        "mssv": mssv_val,
        "nganh": data.nganh,
        "mon": data.mon,
        "ly_do_rot": data.ly_do_rot
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result_data = response.json()
        
        # Lưu vào database
        new_roadmap = AIRoadmap2(
            MSSV=str(data.mssv),
            mon_hoc=data.mon,
            ly_do_rot=data.ly_do_rot,
            loi_khuyen=result_data.get("loi_khuyen", ""),
            tuan_1=result_data.get("tuan_1", ""),
            tuan_2=result_data.get("tuan_2", "")
        )
        db.add(new_roadmap)
        db.commit()
        
        # Trả về kết hợp thông tin input để frontend hiển thị nếu cần
        result_data["mon_hoc"] = data.mon
        result_data["ly_do_rot"] = data.ly_do_rot
        return result_data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi AI API Roadmap: {str(e)}")

# ─────────────────────────────────────────────────────────────────
#  KHẢO SÁT TÂM LÝ & THÓI QUEN (300 câu hỏi)
# ─────────────────────────────────────────────────────────────────

import random

@router.get("/tam-ly/random/{mssv}")
def get_random_tamly(mssv: str, db: Session = Depends(get_db_v2)):
    """Lấy 30 câu hỏi ngẫu nhiên chưa từng làm cho sinh viên"""
    done_ids = db.query(LichSuTestTamLy2.cau_hoi_id).filter(LichSuTestTamLy2.mssv == mssv).all()
    done_ids_list = [id[0] for id in done_ids]

    query = db.query(CauHoiTamLy2)
    if done_ids_list:
        query = query.filter(~CauHoiTamLy2.id.in_(done_ids_list))
    
    available_questions = query.all()
    
    unique_questions = []
    seen_texts = set()
    for q in available_questions:
        text = q.cau_hoi.strip().lower()
        if text not in seen_texts:
            seen_texts.add(text)
            unique_questions.append(q)
            
    selected = random.sample(unique_questions, min(len(unique_questions), 30))
    
    return {
        "questions": [
            {
                "id": q.id,
                "thuoc_tinh": q.thuoc_tinh,
                "question": q.cau_hoi,
                "options": q.options,
                "explanation": q.giai_thich
            } for q in selected
        ],
        "total": len(selected)
    }


class SubmitTamLyRequest(BaseModel):
    mssv: str
    answers: dict  # { "question_id_str": chosen_index }

@router.post("/tam-ly/submit")
def submit_tamly(data: SubmitTamLyRequest, db: Session = Depends(get_db_v2)):
    """Chấm điểm bài test tâm lý và lưu lịch sử"""
    total_score = 0
    total_questions = len(data.answers)
    correct_count = 0
    results = {}

    for q_id_str, chosen_idx in data.answers.items():
        q_id = int(q_id_str)
        q = db.query(CauHoiTamLy2).filter(CauHoiTamLy2.id == q_id).first()
        if not q:
            continue
            
        is_correct = (chosen_idx == q.correct_index)
        if is_correct:
            correct_count += 1
            total_score += q.diem_so
            
        lich_su = LichSuTestTamLy2(
            mssv=data.mssv,
            cau_hoi_id=q_id,
            chosen_index=chosen_idx,
            is_correct=is_correct
        )
        db.add(lich_su)
        
        results[q_id] = {
            "is_correct": is_correct,
            "correct_index": q.correct_index,
            "explanation": q.giai_thich
        }
        
    db.commit()
    
    score_percent = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0
    
    return {
        "total_score": total_score,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "score_percent": score_percent,
        "results": results
    }

@router.get("/tam-ly/stats/{mssv}")
def get_tamly_stats(mssv: str, db: Session = Depends(get_db_v2)):
    """Lấy thống kê làm bài kiểm tra tâm lý của sinh viên"""
    history = db.query(LichSuTestTamLy2).filter(LichSuTestTamLy2.mssv == mssv).all()
    if not history:
        return {"total_questions": 0, "correct_count": 0, "score_percent": 0}
    
    total_questions = len(history)
    correct_count = sum(1 for h in history if h.is_correct)
    score_percent = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0
    
    return {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "score_percent": score_percent
    }


