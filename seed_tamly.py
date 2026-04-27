import json
from app.database_v2 import engine_v2, SessionLocalV2
from app.models.student_risk_v2 import Base2, CauHoiTamLy2

# Tạo bảng
print("Tạo bảng CauHoiTamLy2 và LichSuTestTamLy2...")
Base2.metadata.create_all(bind=engine_v2)

# Dữ liệu mẫu (30 câu hỏi về tâm lý, thời gian, chuyên cần...)
# Dựa trên 13 thuộc tính. Ở đây tạo nhanh 30 câu để test.
sample_questions = [
    {
        "thuoc_tinh": "chuyen_can",
        "cau_hoi": f"Bạn cảm thấy thế nào khi chuông báo thức reo vào buổi sáng lúc đi học? (Câu {i})",
        "options": [
            "Lập tức dậy ngay vì sợ trễ",
            "Ngủ nướng thêm 5 phút rồi dậy",
            "Tắt báo thức ngủ tiếp, trễ thì nghỉ luôn",
            "Cảm thấy mệt mỏi và kiệt sức không muốn đến lớp"
        ],
        "correct_index": 0,
        "diem_so": 1,
        "giai_thich": "Dậy ngay khi chuông reo thể hiện kỷ luật bản thân tốt."
    } for i in range(1, 11)
] + [
    {
        "thuoc_tinh": "thoi_gian_tu_hoc",
        "cau_hoi": f"Khi ngồi vào bàn tự học, điều gì thường làm bạn phân tâm nhất? (Câu {i})",
        "options": [
            "Điện thoại và mạng xã hội",
            "Tiếng ồn từ xung quanh",
            "Không biết bắt đầu từ đâu",
            "Tôi hiếm khi bị phân tâm vì áp dụng Pomodoro"
        ],
        "correct_index": 3,
        "diem_so": 1,
        "giai_thich": "Sử dụng kỹ thuật Pomodoro giúp duy trì tập trung lâu dài."
    } for i in range(1, 11)
] + [
    {
        "thuoc_tinh": "ap_luc",
        "cau_hoi": f"Bạn đối phó với áp lực điểm số và thi cử như thế nào? (Câu {i})",
        "options": [
            "Lên kế hoạch ôn tập chia nhỏ từng ngày",
            "Chơi game hoặc xem phim để quên đi",
            "Thức trắng đêm trước ngày thi để học nhồi nhét",
            "Hoảng loạn và than vãn với bạn bè"
        ],
        "correct_index": 0,
        "diem_so": 1,
        "giai_thich": "Chia nhỏ khối lượng công việc là cách tốt nhất để giảm áp lực tâm lý."
    } for i in range(1, 11)
]

def seed_data():
    db = SessionLocalV2()
    try:
        # Xóa cũ
        db.query(CauHoiTamLy2).delete()
        db.commit()

        # Thêm mới
        for q in sample_questions:
            db_q = CauHoiTamLy2(
                thuoc_tinh=q["thuoc_tinh"],
                cau_hoi=q["cau_hoi"],
                options=q["options"],
                correct_index=q["correct_index"],
                diem_so=q["diem_so"],
                giai_thich=q["giai_thich"]
            )
            db.add(db_q)
        db.commit()
        print(f"Đã import thành công {len(sample_questions)} câu hỏi tâm lý mẫu.")
    except Exception as e:
        print("Lỗi:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
