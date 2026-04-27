import random
from app.database_v2 import engine_v2, SessionLocalV2
from app.models.student_risk_v2 import Base2, CauHoiTamLy2, LichSuTestTamLy2

# 13 thuộc tính rủi ro
features = [
    "thoi_gian_tu_hoc", "chuyen_can", "diem_qua_trinh", 
    "hoan_thanh_bai_tap", "tre_hoc", "loai_mon_hoc", 
    "tai_lieu_on_tap", "hinh_thuc_thi", "tre_hoc_phi", 
    "ho_tro", "hoc_nhom", "lam_them", "co_kinh_nghiem"
]

# Các mẫu câu hỏi và đáp án (tương ứng chung cho từng chủ đề để sinh tự động)
templates = {
    "thoi_gian_tu_hoc": [
        ("Bạn thường làm gì khi cảm thấy mất tập trung lúc tự học?", ["Áp dụng Pomodoro 25 phút", "Lướt điện thoại 1 chút", "Ngủ luôn", "Cố gắng nhồi nhét"], 0, "Pomodoro giúp não bộ nghỉ ngơi hợp lý."),
        ("Cách bạn sắp xếp thời gian tự học trong tuần là:", ["Lên thời gian biểu cố định", "Rảnh lúc nào học lúc đó", "Đợi sát ngày thi mới học", "Không tự học"], 0, "Thời gian biểu cố định tạo thói quen tốt."),
    ],
    "chuyen_can": [
        ("Sáng nay trời mưa to và bạn có tiết học lúc 7h, bạn sẽ:", ["Mặc áo mưa đi học đúng giờ", "Đợi tạnh mưa rồi đi, trễ chút không sao", "Nhờ bạn điểm danh hộ", "Nghỉ luôn ở nhà ngủ"], 0, "Chuyên cần thể hiện thái độ nghiêm túc với việc học."),
        ("Khi biết mình sẽ vắng học vì lý do chính đáng, bạn sẽ:", ["Gửi email xin phép giảng viên", "Nhờ bạn báo cáo", "Không làm gì cả", "Lên lớp bù vào hôm khác mà không báo"], 0, "Gửi email xin phép thể hiện sự tôn trọng."),
    ],
    "diem_qua_trinh": [
        ("Nếu bài kiểm tra giữa kỳ điểm thấp, bạn sẽ:", ["Tìm hiểu nguyên nhân và hỏi giảng viên", "Mặc kệ vì còn thi cuối kỳ", "Thất vọng và chán nản", "Trách đề thi quá khó"], 0, "Nhận biết điểm yếu giúp cải thiện điểm số ở các bài sau."),
        ("Để cải thiện điểm quá trình, bạn thường ưu tiên:", ["Làm bài tập đầy đủ và phát biểu", "Chỉ đến điểm danh", "Chờ cuối kỳ gỡ điểm", "Xin giảng viên nâng điểm"], 0, "Quá trình học tập tích lũy từ các việc nhỏ hàng ngày."),
    ],
    "hoan_thanh_bai_tap": [
        ("Khi gặp một bài tập khó không giải được, bạn sẽ:", ["Hỏi bạn bè hoặc tìm tài liệu tham khảo", "Bỏ trống", "Chép bài của bạn", "Nộp trễ hạn"], 0, "Kỹ năng tìm kiếm tài liệu là cực kỳ quan trọng."),
        ("Bạn có thói quen làm bài tập về nhà khi nào?", ["Làm ngay trong ngày được giao", "Để đến cuối tuần làm một thể", "Đợi tối hôm trước ngày nộp mới làm", "Đợi bạn làm xong rồi mượn"], 0, "Làm ngay giúp kiến thức còn mới và in sâu vào trí nhớ."),
    ],
    "tre_hoc": [
        ("Để không bị đi trễ vào buổi sáng, bạn thường:", ["Chuẩn bị đồ từ tối hôm trước", "Sáng dậy mới cuống cuồng chuẩn bị", "Phụ thuộc vào người khác gọi dậy", "Cài 10 cái báo thức nhưng vẫn tắt đi ngủ tiếp"], 0, "Chuẩn bị trước giúp bạn chủ động thời gian."),
        ("Lý do chính khiến bạn đi học trễ thường là gì?", ["Kẹt xe / hỏng xe (khách quan)", "Thức khuya dậy muộn", "Cố tình đi trễ vì lười", "Không biết đường"], 1, "Thức khuya là nguyên nhân chủ quan phổ biến nhất, cần điều chỉnh."),
    ],
    "loai_mon_hoc": [
        ("Đối với các môn đại cương khô khan, bạn thường:", ["Liên hệ kiến thức với thực tế", "Học vẹt để qua môn", "Ngủ gật trong lớp", "Bỏ học nhiều"], 0, "Môn đại cương là nền tảng tư duy quan trọng."),
        ("Khi học môn chuyên ngành khó, bạn làm thế nào để hiểu bài?", ["Thực hành nhiều và hỏi giảng viên", "Chỉ đọc lướt slide", "Đợi bạn chỉ lại", "Không quan tâm lắm"], 0, "Thực hành là cách tốt nhất để tiếp thu chuyên ngành."),
    ],
    "tai_lieu_on_tap": [
        ("Trước kỳ thi, bạn thường tìm tài liệu ôn tập ở đâu?", ["Thư viện và kho tài liệu của trường", "Xin từ anh chị khóa trên", "Chỉ học slide giảng viên", "Không cần tài liệu"], 0, "Tài liệu chính thống từ thư viện luôn đảm bảo chất lượng."),
        ("Khi đọc một cuốn giáo trình dày, bạn sẽ:", ["Đọc mục lục và tóm tắt ý chính", "Đọc từ trang 1 đến cuối", "Đọc lướt không hiểu gì", "Chỉ đọc phần thầy cô bôi đậm"], 0, "Đọc mục lục giúp nắm tổng quan cấu trúc kiến thức."),
    ],
    "hinh_thuc_thi": [
        ("Khi thi trắc nghiệm, chiến thuật của bạn là:", ["Làm câu dễ trước, câu khó sau", "Làm từ trên xuống dưới", "Đánh lụi ngay từ đầu", "Làm câu khó trước"], 0, "Câu dễ lấy điểm trước giúp tiết kiệm thời gian và tạo tâm lý tốt."),
        ("Với bài thi tự luận, điều quan trọng nhất theo bạn là:", ["Trình bày rõ ý và logic", "Viết càng dài càng tốt", "Chữ đẹp là được", "Viết đúng y hệt sách giáo khoa"], 0, "Giảng viên chấm ý và tư duy logic của sinh viên."),
    ],
    "tre_hoc_phi": [
        ("Nếu gặp khó khăn về tài chính, bạn sẽ xử lý thế nào để đóng học phí?", ["Tìm việc làm thêm bán thời gian", "Vay mượn lãi suất cao", "Bỏ học", "Phó mặc cho hoàn cảnh"], 0, "Chủ động tài chính bằng việc làm thêm hợp lý là kỹ năng sống."),
        ("Khi có thông báo đóng học phí, bạn thường:", ["Lên kế hoạch tiết kiệm từ trước", "Đợi sát hạn mới xin gia đình", "Phớt lờ thông báo", "Tiêu xài hết tiền rồi mới lo"], 0, "Kế hoạch tài chính giúp bạn không bị động."),
    ],
    "ho_tro": [
        ("Khi gặp rắc rối về tâm lý hoặc học tập, bạn sẽ tìm đến ai?", ["Phòng Đào tạo / Cán bộ tư vấn tâm lý", "Giữ kín trong lòng", "Than vãn trên mạng xã hội", "Bỏ học để giải tỏa"], 0, "Chuyên viên tư vấn luôn sẵn sàng hỗ trợ bạn một cách chuyên nghiệp."),
        ("Bạn nghĩ gì về việc xin hỗ trợ từ giảng viên?", ["Đó là quyền lợi và nên làm", "Giảng viên rất khó tính, không nên hỏi", "Chỉ những người yếu kém mới cần", "Làm phiền giảng viên"], 0, "Giảng viên luôn khuyến khích sinh viên đặt câu hỏi."),
    ],
    "hoc_nhom": [
        ("Khi tham gia làm bài tập nhóm, bạn thường nhận vai trò gì?", ["Chủ động nhận việc phù hợp khả năng", "Đợi nhóm trưởng phân công", "Không làm gì cả, dựa dẫm", "Chỉ làm phần dễ nhất"], 0, "Sự chủ động là chìa khóa của làm việc nhóm hiệu quả."),
        ("Nếu nhóm có thành viên lười biếng, bạn sẽ xử lý sao?", ["Nhắc nhở nhẹ nhàng và tìm hiểu lý do", "Làm thay luôn cho xong", "Cãi nhau với bạn đó", "Báo thẳng với giảng viên mà không nói chuyện trước"], 0, "Kỹ năng giao tiếp và thấu hiểu giúp giải quyết xung đột."),
    ],
    "lam_them": [
        ("Việc làm thêm ảnh hưởng đến việc học của bạn như thế nào?", ["Tôi biết cân bằng thời gian", "Làm thêm khiến tôi kiệt sức", "Tôi cúp học để đi làm", "Tôi không có thời gian ôn thi"], 0, "Cân bằng thời gian là kỹ năng quan trọng nhất khi đi làm thêm."),
        ("Mục tiêu chính của việc bạn đi làm thêm là gì?", ["Tích lũy kinh nghiệm và trang trải một phần", "Chỉ để kiếm tiền tiêu xài", "Vì bạn bè rủ đi", "Để trốn việc học"], 0, "Kinh nghiệm từ việc làm thêm rất có giá trị cho CV sau này."),
    ],
    "co_kinh_nghiem": [
        ("Bạn tiếp cận các kinh nghiệm thực tế trong ngành như thế nào?", ["Tham gia CLB học thuật và xin thực tập sớm", "Đợi trường sắp xếp đi thực tập", "Chỉ học lý thuyết là đủ", "Đi làm các công việc không liên quan"], 0, "CLB học thuật là môi trường thực hành tuyệt vời."),
        ("Khi một nhà tuyển dụng hỏi về kinh nghiệm, bạn sẽ nói gì nếu chưa có?", ["Nêu bật các dự án môn học và kỹ năng mềm", "Nói dối là đã có", "Tự ti và không biết trả lời", "Trách trường không dạy thực hành"], 0, "Dự án môn học hoàn toàn có thể coi là kinh nghiệm thực tế ban đầu."),
    ]
}

def generate_300_questions():
    questions = []
    # 13 chủ đề, ta cần khoảng 300 câu => mỗi chủ đề ~ 23 câu
    # Lặp qua từng chủ đề
    for feature in features:
        feature_templates = templates.get(feature, templates["chuyen_can"]) # fallback
        for i in range(1, 25): # 24 câu mỗi feature
            # Chọn template luân phiên
            tpl = feature_templates[i % len(feature_templates)]
            cau_hoi_goc = tpl[0]
            options = tpl[1]
            correct_idx = tpl[2]
            explanation = tpl[3]
            
            # Thêm mã (Variation) để phân biệt
            cau_hoi_moi = f"{cau_hoi_goc} (Biến thể #{i})"
            
            questions.append({
                "thuoc_tinh": feature,
                "cau_hoi": cau_hoi_moi,
                "options": options,
                "correct_index": correct_idx,
                "diem_so": 1,
                "giai_thich": explanation
            })
            
            if len(questions) == 300:
                break
        if len(questions) == 300:
            break
            
    return questions

def seed_data():
    db = SessionLocalV2()
    try:
        print("Đang xóa lịch sử và câu hỏi cũ...")
        db.query(LichSuTestTamLy2).delete()
        db.query(CauHoiTamLy2).delete()
        db.commit()

        questions_data = generate_300_questions()
        print(f"Đã tạo {len(questions_data)} câu hỏi. Đang import vào Database...")

        for q in questions_data:
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
        print("Import thành công 300 câu hỏi tâm lý.")
    except Exception as e:
        print("Lỗi:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
