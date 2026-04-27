"""
Learning Engine — Sinh lộ trình học tập & bài tập trắc nghiệm
dựa trên warning_reasons từ kết quả dự báo AI.
Mỗi key rủi ro → 1 lộ trình + 3-5 câu hỏi trắc nghiệm.
"""
from typing import List, Dict, Any

# ─────────────────────────────────────────────────────────────────
# BẢNG NỘI DUNG — 13 RỦI RO × (LỘ TRÌNH + BÀI TẬP)
# ─────────────────────────────────────────────────────────────────

RISK_CONTENT_MAP: Dict[str, Dict[str, Any]] = {
    "chuyen_can": {
        "label": "Tỉ lệ chuyên cần thấp",
        "muc_tieu": "Nâng tỉ lệ có mặt lên trên 80% trong 4 tuần tới",
        "hanh_dong": [
            "Đặt báo thức nhắc nhở 30 phút trước giờ học",
            "Lập kế hoạch đi học theo lịch tuần",
            "Nhờ bạn học cùng nhắc nhở khi vắng mặt",
            "Theo dõi điểm danh hàng tuần và tự đánh giá"
        ],
        "questions": [
            {
                "question": "Điểm danh ảnh hưởng thế nào đến kết quả học tập?",
                "options": [
                    "Không ảnh hưởng gì cả",
                    "Ảnh hưởng trực tiếp đến điểm quá trình và khả năng học tập",
                    "Chỉ ảnh hưởng đến giáo viên",
                    "Chỉ quan trọng vào kỳ thi"
                ],
                "correct_index": 1,
                "explanation": "Chuyên cần giúp bạn tiếp thu kiến thức đầy đủ, tham gia thảo luận và được tính điểm quá trình. Vắng nhiều dẫn đến mất kiến thức, giảm điểm và nguy cơ trượt môn."
            },
            {
                "question": "Khi bạn biết mình sẽ nghỉ học vì lý do chính đáng, điều nên làm là?",
                "options": [
                    "Không cần báo ai cả",
                    "Nhắn tin xin phép giảng viên và mượn vở bạn học",
                    "Chờ đến buổi sau rồi giải thích",
                    "Bỏ luôn cả tuần cho tiện"
                ],
                "correct_index": 1,
                "explanation": "Thông báo trước thể hiện trách nhiệm và giúp giảng viên ghi nhận lý do vắng. Mượn vở bạn đảm bảo bạn không bị hổng kiến thức."
            },
            {
                "question": "Chiến lược nào giúp duy trì chuyên cần tốt nhất?",
                "options": [
                    "Học theo hứng",
                    "Để đến lúc gần thi mới nghiêm túc",
                    "Lập lịch cố định và cam kết từ đầu học kỳ",
                    "Nhờ bạn điểm danh hộ"
                ],
                "correct_index": 2,
                "explanation": "Lịch học cố định từ đầu học kỳ tạo thói quen bền vững và giảm nguy cơ vắng tự phát."
            }
        ]
    },

    "thoi_gian_tu_hoc": {
        "label": "Thời gian tự học không đủ",
        "muc_tieu": "Đạt ít nhất 2 giờ tự học/ngày trong 3 tuần liên tiếp",
        "hanh_dong": [
            "Chọn 1 khung giờ cố định mỗi ngày để tự học (vd: 19h-21h)",
            "Tắt điện thoại hoặc dùng chế độ focus khi học",
            "Chia nhỏ bài học thành các phần 25 phút (Pomodoro)",
            "Ghi lại số giờ học mỗi ngày để theo dõi"
        ],
        "questions": [
            {
                "question": "Phương pháp Pomodoro là gì?",
                "options": [
                    "Học liên tục không nghỉ suốt 3 tiếng",
                    "Học 25 phút, nghỉ 5 phút, lặp lại",
                    "Chỉ học vào ban đêm",
                    "Học theo nhóm bắt buộc"
                ],
                "correct_index": 1,
                "explanation": "Pomodoro (25 phút học + 5 phút nghỉ) giúp duy trì tập trung, tránh mệt mỏi và tăng hiệu suất học tập đáng kể."
            },
            {
                "question": "Khoảng thời gian tự học khuyến nghị mỗi ngày cho sinh viên là?",
                "options": [
                    "15-30 phút",
                    "30-60 phút",
                    "2-4 giờ",
                    "Trên 8 giờ"
                ],
                "correct_index": 2,
                "explanation": "Nghiên cứu giáo dục khuyến nghị sinh viên tự học từ 2-4 giờ/ngày để đủ thời gian ôn luyện và làm bài tập."
            },
            {
                "question": "Điều nào gây giảm hiệu quả tự học nhất?",
                "options": [
                    "Học trong môi trường yên tĩnh",
                    "Vừa học vừa dùng mạng xã hội",
                    "Lên kế hoạch học trước",
                    "Nghỉ giải lao đúng giờ"
                ],
                "correct_index": 1,
                "explanation": "Mạng xã hội phân tán sự tập trung và kéo dài thời gian học mà không hiệu quả. Mỗi lần bị phân tâm mất trung bình 23 phút để tập trung lại."
            }
        ]
    },

    "diem_qua_trinh": {
        "label": "Điểm quá trình thấp",
        "muc_tieu": "Nâng điểm quá trình lên trên 6.0 trong học kỳ này",
        "hanh_dong": [
            "Xem lại rubric chấm điểm của từng môn học",
            "Nộp đầy đủ và đúng hạn tất cả bài tập",
            "Chủ động hỏi giảng viên về cách cải thiện điểm",
            "Tham gia đầy đủ các buổi thảo luận nhóm và trình bày"
        ],
        "questions": [
            {
                "question": "Khi điểm quá trình thấp, bước đầu tiên nên làm là?",
                "options": [
                    "Bỏ qua và hy vọng điểm thi bù đắp",
                    "Liên hệ giảng viên để hiểu nguyên nhân và cách cải thiện",
                    "Khiếu nại liên tục",
                    "Đổi sang môn khác"
                ],
                "correct_index": 1,
                "explanation": "Gặp giảng viên giúp bạn hiểu điểm bị trừ ở đâu và có kế hoạch cải thiện cụ thể ngay từ sớm."
            },
            {
                "question": "Điểm quá trình thường chiếm bao nhiêu phần trăm trong thang điểm?",
                "options": [
                    "0-10%",
                    "10-20%",
                    "30-50%",
                    "100%"
                ],
                "correct_index": 2,
                "explanation": "Tùy môn học, điểm quá trình thường chiếm 30-50% tổng điểm. Đây là lợi thế cạnh tranh so với chỉ trông chờ vào thi cuối kỳ."
            },
            {
                "question": "Cách nào giúp cải thiện điểm quá trình hiệu quả nhất?",
                "options": [
                    "Chỉ học vào đêm trước khi nộp bài",
                    "Nộp bài đúng hạn, đủ yêu cầu, chất lượng cao và tham gia thảo luận",
                    "Sao chép bài bạn vì tiết kiệm thời gian",
                    "Xin giảng viên nâng điểm"
                ],
                "correct_index": 1,
                "explanation": "Nộp đúng hạn tránh mất điểm phạt. Chất lượng + tham gia tích cực là yếu tố quan trọng nhất để được điểm cao."
            }
        ]
    },

    "hoan_thanh_bai_tap": {
        "label": "Tỉ lệ hoàn thành bài tập thấp",
        "muc_tieu": "Hoàn thành trên 90% bài tập được giao trong 4 tuần tới",
        "hanh_dong": [
            "Ghi tất cả deadline bài tập vào lịch ngay khi được giao",
            "Chia bài tập lớn thành các phần nhỏ, làm dần mỗi ngày",
            "Dành 30 phút đầu buổi tự học chỉ để làm bài tập",
            "Lập nhóm bạn kiểm tra tiến độ lẫn nhau"
        ],
        "questions": [
            {
                "question": "Tại sao hoàn thành bài tập đúng hạn quan trọng?",
                "options": [
                    "Chỉ để đối phó với giảng viên",
                    "Giúp ôn luyện kiến thức liên tục, được điểm và rèn kỷ luật",
                    "Không quan trọng, chỉ cần thi tốt",
                    "Vì bạn bè ai cũng làm thì mình phải làm"
                ],
                "correct_index": 1,
                "explanation": "Bài tập là công cụ luyện tập củng cố kiến thức. Hoàn thành đầy đủ = điểm quá trình tốt + nền tảng vững cho kỳ thi."
            },
            {
                "question": "Khi có quá nhiều bài tập cùng lúc, nên làm gì?",
                "options": [
                    "Bỏ hết và nghỉ ngơi",
                    "Làm bài nào dễ trước, bỏ bài khó",
                    "Ưu tiên theo deadline gần nhất và mức độ quan trọng",
                    "Chép bài bạn cho nhanh"
                ],
                "correct_index": 2,
                "explanation": "Ưu tiên theo deadline và trọng số điểm giúp bạn quản lý thời gian hiệu quả và tránh mất điểm oan vì trễ hạn."
            }
        ]
    },

    "loai_mon_hoc": {
        "label": "Loại môn học có độ khó cao",
        "muc_tieu": "Nắm vững phương pháp học phù hợp với đặc thù môn học",
        "hanh_dong": [
            "Xác định rõ đặc thù môn (lý thuyết, thực hành, toán, code...)",
            "Tìm tài liệu và video hướng dẫn chuyên biệt cho môn đó",
            "Lập nhóm học với bạn cùng môn để giải đáp thắc mắc",
            "Ôn luyện thêm sau giờ học ngay trong ngày"
        ],
        "questions": [
            {
                "question": "Môn học chuyên ngành khác gì với môn đại cương?",
                "options": [
                    "Không có gì khác nhau",
                    "Thường đòi hỏi kiến thức nền và kỹ năng ứng dụng thực tế cao hơn",
                    "Dễ hơn vì gần với nghề nghiệp",
                    "Không cần học lý thuyết"
                ],
                "correct_index": 1,
                "explanation": "Môn chuyên ngành xây dựng trên nền tảng đại cương và đòi hỏi ứng dụng thực tế, cần chiến lược học sâu hơn."
            },
            {
                "question": "Chiến lược học hiệu quả cho môn kỹ thuật/toán là?",
                "options": [
                    "Đọc tài liệu một lần là xong",
                    "Luyện tập nhiều bài tập và hiểu bản chất từng bước giải",
                    "Chỉ học công thức mà không hiểu ý nghĩa",
                    "Sao chép đáp án"
                ],
                "correct_index": 1,
                "explanation": "Môn kỹ thuật đòi hỏi luyện tập và hiểu sâu từng bước. Chỉ học lý thuyết mà không luyện tập không đủ."
            }
        ]
    },

    "tai_lieu_on_tap": {
        "label": "Thiếu tài liệu ôn tập",
        "muc_tieu": "Tìm đủ tài liệu chất lượng cho từng môn học trong 1 tuần",
        "hanh_dong": [
            "Hỏi giảng viên về giáo trình và nguồn tài liệu gợi ý",
            "Tìm kiếm trên thư viện trường và các nền tảng như Coursera, edX",
            "Liên hệ với sinh viên khoá trên để xin tài liệu",
            "Tạo nhóm chia sẻ tài liệu với bạn cùng lớp"
        ],
        "questions": [
            {
                "question": "Nguồn tài liệu học tập đáng tin cậy nhất là?",
                "options": [
                    "Bất kỳ trang web nào trên Google",
                    "Giáo trình chính thức do trường/giảng viên cung cấp và nguồn học thuật uy tín",
                    "Chỉ dùng Wikipedia",
                    "Tài liệu từ mạng xã hội"
                ],
                "correct_index": 1,
                "explanation": "Giáo trình chính thức đảm bảo phù hợp với chương trình. Nguồn học thuật (sách, journal) đảm bảo độ chính xác."
            },
            {
                "question": "Khi không có tài liệu ôn tập, bước tiếp theo nên là?",
                "options": [
                    "Không học gì cả",
                    "Liên hệ giảng viên hoặc bạn học để được hỗ trợ ngay",
                    "Chờ đến gần thi mới lo",
                    "Tìm đề thi cũ mà không hiểu nội dung"
                ],
                "correct_index": 1,
                "explanation": "Chủ động xin hỗ trợ sớm giúp bạn không bị hổng kiến thức và có thời gian ôn luyện đầy đủ."
            }
        ]
    },

    "hinh_thuc_thi": {
        "label": "Chưa làm quen với hình thức thi",
        "muc_tieu": "Luyện tập theo đúng hình thức thi của từng môn trước kỳ thi 3 tuần",
        "hanh_dong": [
            "Xác nhận hình thức thi (trắc nghiệm, tự luận, thực hành, vấn đáp)",
            "Tìm đề thi cũ và luyện tập theo hình thức đó",
            "Tập quản lý thời gian theo số câu và thời gian thực thi",
            "Thực hành ít nhất 2-3 đề thi cũ hoàn chỉnh trước kỳ thi"
        ],
        "questions": [
            {
                "question": "Tại sao cần biết hình thức thi trước khi ôn tập?",
                "options": [
                    "Không cần thiết, cứ học đều là được",
                    "Để chọn chiến lược ôn tập phù hợp (trắc nghiệm khác tự luận)",
                    "Chỉ để đỡ lo lắng",
                    "Giảng viên bắt buộc"
                ],
                "correct_index": 1,
                "explanation": "Thi trắc nghiệm cần nhận dạng và loại trừ nhanh; tự luận cần trình bày sâu; thực hành cần kỹ năng. Chiến lược ôn khác nhau hoàn toàn."
            },
            {
                "question": "Cách tốt nhất để chuẩn bị cho thi tự luận là?",
                "options": [
                    "Học thuộc lòng toàn bộ tài liệu",
                    "Hiểu sâu bản chất, luyện viết trình bày rõ ràng và có cấu trúc",
                    "Chỉ đọc đề cương",
                    "Đọc 1 lần đủ rồi"
                ],
                "correct_index": 1,
                "explanation": "Thi tự luận đánh giá khả năng tư duy và trình bày. Cần luyện tập viết, không chỉ đọc."
            }
        ]
    },

    "tre_hoc_phi": {
        "label": "Trễ học phí gây áp lực",
        "muc_tieu": "Giải quyết tình trạng học phí trong vòng 2 tuần để yên tâm học",
        "hanh_dong": [
            "Liên hệ phòng tài vụ để biết các phương án gia hạn",
            "Tìm hiểu học bổng và hỗ trợ tài chính từ trường",
            "Trao đổi với gia đình để có kế hoạch tài chính rõ ràng",
            "Tránh để vấn đề tài chính ảnh hưởng đến tập trung học"
        ],
        "questions": [
            {
                "question": "Khi gặp khó khăn học phí, sinh viên nên làm gì đầu tiên?",
                "options": [
                    "Bỏ học ngay",
                    "Liên hệ phòng công tác sinh viên/tài vụ để tìm hỗ trợ",
                    "Vay tiền ngân hàng đen",
                    "Im lặng và tự chịu"
                ],
                "correct_index": 1,
                "explanation": "Trường có nhiều chính sách hỗ trợ: hoãn nộp, học bổng khó khăn, vay vốn sinh viên. Liên hệ sớm tránh mất quyền học."
            },
            {
                "question": "Nguồn hỗ trợ tài chính uy tín nhất cho sinh viên là?",
                "options": [
                    "Ứng dụng vay tiền online không rõ nguồn gốc",
                    "Học bổng nhà trường, vay vốn Ngân hàng Chính sách Xã hội",
                    "Vay nặng lãi",
                    "Không có nguồn nào"
                ],
                "correct_index": 1,
                "explanation": "Học bổng và vay vốn NHCSXH lãi suất ưu đãi là những kênh an toàn và hợp pháp dành riêng cho sinh viên."
            }
        ]
    },

    "ho_tro": {
        "label": "Thiếu hỗ trợ trong học tập",
        "muc_tieu": "Xây dựng mạng lưới hỗ trợ học tập hiệu quả trong 2 tuần",
        "hanh_dong": [
            "Tham gia ít nhất 1 nhóm học tập hoặc CLB học thuật",
            "Liên hệ phòng hỗ trợ sinh viên để được tư vấn",
            "Chủ động hỏi giảng viên trong và sau giờ học",
            "Kết nối với sinh viên cùng ngành để chia sẻ kinh nghiệm"
        ],
        "questions": [
            {
                "question": "Tại sao hỗ trợ học tập từ bạn bè và thầy cô quan trọng?",
                "options": [
                    "Vì không ai có thể học một mình",
                    "Giúp giải đáp thắc mắc nhanh, học từ kinh nghiệm người khác và không cảm thấy cô đơn",
                    "Chỉ để có bạn chơi",
                    "Không quan trọng nếu bạn thông minh"
                ],
                "correct_index": 1,
                "explanation": "Nghiên cứu chỉ ra sinh viên có mạng lưới hỗ trợ tốt có kết quả học tập tốt hơn và ít bỏ học hơn đáng kể."
            },
            {
                "question": "Khi không hiểu bài, hành động tốt nhất là?",
                "options": [
                    "Mặc kệ và tiếp tục",
                    "Hỏi ngay giảng viên hoặc bạn học, không để tồn đọng",
                    "Chờ đến lúc thi mới xem lại",
                    "Bỏ môn đó"
                ],
                "correct_index": 1,
                "explanation": "Kiến thức thường xây dựng tuần tự. Để tồn đọng thắc mắc sẽ gây ra lỗ kiến thức lớn dần theo từng tuần."
            }
        ]
    },

    "tre_hoc": {
        "label": "Hay đến trễ giờ học",
        "muc_tieu": "Giảm số lần trễ xuống 0 trong 3 tuần liên tiếp",
        "hanh_dong": [
            "Chuẩn bị đồ dùng học tập từ tối hôm trước",
            "Đặt báo thức sớm hơn 15-20 phút thực tế cần",
            "Tính toán lại thời gian di chuyển và dự phòng tắc đường",
            "Ngủ đúng giờ để dậy đúng giờ"
        ],
        "questions": [
            {
                "question": "Đến trễ ảnh hưởng gì đến học tập?",
                "options": [
                    "Không ảnh hưởng gì",
                    "Mất nội dung đầu buổi, có thể bị đánh dấu vắng và ảnh hưởng đến điểm chuyên cần",
                    "Chỉ ảnh hưởng đến bạn cùng lớp",
                    "Giảng viên không để ý"
                ],
                "correct_index": 1,
                "explanation": "Phần đầu buổi học thường là phần tóm tắt và giới thiệu nội dung quan trọng. Trễ liên tục cũng có thể bị tính vắng."
            },
            {
                "question": "Cách hiệu quả nhất để không bị trễ học là?",
                "options": [
                    "Đặt 10 báo thức liên tiếp",
                    "Ngủ sớm và chuẩn bị sẵn sàng từ hôm trước, tính thêm thời gian dự phòng",
                    "Uống nhiều cà phê",
                    "Nhờ giảng viên cho vào muộn"
                ],
                "correct_index": 1,
                "explanation": "Chuẩn bị trước + ngủ đủ giấc là nền tảng. Tính thêm buffer time 15-20 phút xử lý mọi tình huống bất ngờ."
            }
        ]
    },

    "hoc_nhom": {
        "label": "Chưa tham gia học nhóm hiệu quả",
        "muc_tieu": "Tham gia hoặc thành lập nhóm học 2-3 người trong tuần này",
        "hanh_dong": [
            "Tìm 2-3 bạn cùng class có mục tiêu học tương tự",
            "Lên lịch học nhóm cố định 2 buổi/tuần",
            "Phân công mỗi người ôn 1 chủ đề rồi giảng lại cho cả nhóm",
            "Dùng nhóm để kiểm tra bài tập lẫn nhau trước khi nộp"
        ],
        "questions": [
            {
                "question": "Học nhóm hiệu quả nhất khi nào?",
                "options": [
                    "Khi tụ tập nói chuyện cả buổi",
                    "Khi mỗi thành viên đã tự học trước và nhóm để giải đáp/kiểm tra",
                    "Chỉ làm bài tập hộ nhau",
                    "Ngồi cạnh nhau nhưng mỗi người làm việc riêng"
                ],
                "correct_index": 1,
                "explanation": "Nhóm học hiệu quả = tự học trước + thảo luận sâu + kiểm tra lẫn nhau. Dạy lại cho người khác là cách học giữ lại kiến thức tốt nhất."
            },
            {
                "question": "Quy mô nhóm học tập lý tưởng là?",
                "options": [
                    "1 người",
                    "2-5 người",
                    "10-15 người",
                    "Cả lớp"
                ],
                "correct_index": 1,
                "explanation": "Nhóm 2-5 người đủ để có nhiều góc nhìn nhưng vẫn dễ điều phối và mỗi người đều có cơ hội phát biểu."
            }
        ]
    },

    "lam_them": {
        "label": "Làm thêm ảnh hưởng đến học tập",
        "muc_tieu": "Cân bằng thời gian làm thêm và học tập để không ảnh hưởng kết quả",
        "hanh_dong": [
            "Tính toán số giờ làm thêm tối đa không ảnh hưởng học: thường ≤ 20h/tuần",
            "Chọn công việc có lịch linh hoạt, không trùng giờ học",
            "Ưu tiên làm thêm liên quan đến ngành học",
            "Trao đổi với gia đình nếu áp lực tài chính quá lớn"
        ],
        "questions": [
            {
                "question": "Số giờ làm thêm tối đa/tuần để không ảnh hưởng học là?",
                "options": [
                    "Không giới hạn",
                    "Dưới 20 giờ/tuần",
                    "Trên 40 giờ/tuần",
                    "5 giờ/tuần"
                ],
                "correct_index": 1,
                "explanation": "Nghiên cứu cho thấy trên 20h/tuần làm thêm bắt đầu ảnh hưởng tiêu cực đến điểm số và sức khoẻ sinh viên."
            },
            {
                "question": "Công việc làm thêm lý tưởng nhất cho sinh viên là?",
                "options": [
                    "Bất kỳ việc nào miễn có tiền",
                    "Việc liên quan đến ngành học, lịch linh hoạt và gần trường",
                    "Công việc ca đêm nhiều tiền",
                    "Không nên làm thêm"
                ],
                "correct_index": 1,
                "explanation": "Làm thêm liên quan ngành vừa kiếm tiền vừa tích lũy kinh nghiệm thực tế, đây là lợi thế kép cho sinh viên."
            }
        ]
    },

    "co_kinh_nghiem": {
        "label": "Thiếu kinh nghiệm thực tế",
        "muc_tieu": "Bổ sung ít nhất 1 hoạt động thực tế trong học kỳ này",
        "hanh_dong": [
            "Đăng ký thực tập hoặc tình nguyện trong lĩnh vực chuyên ngành",
            "Tham gia dự án nghiên cứu với giảng viên",
            "Làm dự án cá nhân hoặc đóng góp vào dự án mã nguồn mở",
            "Tham gia CLB chuyên ngành và hackathon/cuộc thi ngành"
        ],
        "questions": [
            {
                "question": "Kinh nghiệm thực tế giúp ích gì trong học tập?",
                "options": [
                    "Không giúp ích gì",
                    "Củng cố lý thuyết, thấy ứng dụng thực tế và tăng động lực học",
                    "Chỉ cần khi đi xin việc",
                    "Làm mất thời gian học"
                ],
                "correct_index": 1,
                "explanation": "Kinh nghiệm thực tế giúp bạn hiểu LÝ DO học lý thuyết, từ đó học có mục tiêu và nhớ lâu hơn đáng kể."
            },
            {
                "question": "Cách tốt nhất để sinh viên năm nhất có kinh nghiệm thực tế là?",
                "options": [
                    "Chờ đến năm cuối",
                    "Tham gia CLB, dự án nhỏ, tình nguyện ngay từ năm 1",
                    "Không cần thiết năm nhất",
                    "Chỉ đọc sách về thực tế"
                ],
                "correct_index": 1,
                "explanation": "Bắt đầu sớm xây dựng portfolio và kỹ năng. Năm cuối bạn sẽ cạnh tranh tốt hơn nhiều so với bạn cùng lớp."
            }
        ]
    }
}

# ─────────────────────────────────────────────────────────────────
#  API: Sinh lộ trình & bài tập dựa trên warning_reasons
# ─────────────────────────────────────────────────────────────────

def _normalize_reason_key(reason: str) -> str:
    """Chuẩn hóa warning_reason về key trong RISK_CONTENT_MAP"""
    reason_lower = str(reason).lower().strip()
    # Map từ warning_reason text → key
    keyword_map = {
        "chuyen_can": ["chuyen_can", "chuyên cần", "tỉ lệ có mặt", "chuyên cần thấp"],
        "thoi_gian_tu_hoc": ["thoi_gian_tu_hoc", "thời gian tự học", "giờ tự học"],
        "diem_qua_trinh": ["diem_qua_trinh", "điểm quá trình", "điểm học tập"],
        "hoan_thanh_bai_tap": ["hoan_thanh_bai_tap", "hoàn thành bài tập", "bài tập"],
        "loai_mon_hoc": ["loai_mon_hoc", "loại môn học", "môn học khó"],
        "tai_lieu_on_tap": ["tai_lieu_on_tap", "tài liệu", "thiếu tài liệu"],
        "hinh_thuc_thi": ["hinh_thuc_thi", "hình thức thi", "hình thức kiểm tra"],
        "tre_hoc_phi": ["tre_hoc_phi", "trễ học phí", "học phí"],
        "ho_tro": ["ho_tro", "hỗ trợ", "thiếu hỗ trợ"],
        "tre_hoc": ["tre_hoc", "trễ học", "đến trễ", "muộn"],
        "hoc_nhom": ["hoc_nhom", "học nhóm"],
        "lam_them": ["lam_them", "làm thêm", "làm việc thêm"],
        "co_kinh_nghiem": ["co_kinh_nghiem", "kinh nghiệm", "thiếu kinh nghiệm"]
    }
    for key, keywords in keyword_map.items():
        if any(kw in reason_lower for kw in keywords):
            return key
    # Thử match trực tiếp
    if reason_lower in RISK_CONTENT_MAP:
        return reason_lower
    return None


def generate_learning_path(mssv: str, pred_result_id: int, warning_reasons: List[str]) -> List[dict]:
    """Sinh danh sách lộ trình học tập"""
    paths = []
    seen_keys = set()

    for reason in warning_reasons:
        key = _normalize_reason_key(reason)
        if not key or key in seen_keys:
            continue
        content = RISK_CONTENT_MAP.get(key)
        if not content:
            continue
        seen_keys.add(key)
        paths.append({
            "MSSV": mssv,
            "prediction_result_id": pred_result_id,
            "risk_reason_key": key,
            "risk_reason_label": content["label"],
            "muc_tieu": content["muc_tieu"],
            "hanh_dong": content["hanh_dong"],
            "status": "todo"
        })

    return paths


def generate_exercises(mssv: str, pred_result_id: int, warning_reasons: List[str]) -> List[dict]:
    """Sinh danh sách bài tập trắc nghiệm"""
    exercises = []
    seen_keys = set()

    for reason in warning_reasons:
        key = _normalize_reason_key(reason)
        if not key or key in seen_keys:
            continue
        content = RISK_CONTENT_MAP.get(key)
        if not content:
            continue
        seen_keys.add(key)

        for q in content.get("questions", []):
            exercises.append({
                "MSSV": mssv,
                "prediction_result_id": pred_result_id,
                "risk_reason_key": key,
                "risk_reason_label": content["label"],
                "question": q["question"],
                "options": q["options"],
                "correct_index": q["correct_index"],
                "explanation": q["explanation"]
            })

    return exercises
