# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Minh Đạt
- **Student ID**: 2A202601142
- **Date**: 28/07/2026
- **Role**: Core Integrator (Role 4 — đầu mối lắp ráp `git pull` code cả nhóm thành 1 app hoàn chỉnh)
---

## I. Technical Contribution (15 Points)

- **Modules Implementated** (vai trò Core Integrator — Role 4: đầu mối lắp ráp `git pull` code của cả nhóm thành 1 app hoàn chỉnh):
  - `src/app.py` — CLI entry point duy nhất: menu 5 lựa chọn (chạy riêng từng level, so sánh cả 3 level trên 1 câu hỏi, chấm batch toàn bộ test case), hàm điều phối `call_level()` gọi đúng `handle_query_*` của từng level do các bạn Role 2/3 cung cấp.
  - `src/server.py` — HTTP API mỏng (Flask) tái sử dụng nguyên `call_level()` từ `app.py`, không viết thêm logic nghiệp vụ mới ở tầng web.
  - `front_end/code.html` — nối giao diện chat tĩnh (do Stitch tạo) thành giao diện động thật: thêm ô nhập câu hỏi, dải chọn Level 1/2/3, JS gọi `fetch('/api/query')` và render bong bóng chat + trace.

- **Code Highlights**:
  - Điểm tôi tâm đắc nhất: `call_level()` trong `app.py` bọc **mọi** lời gọi `handle_query_*` trong try/except, trả về dict lỗi có cùng schema với dict thành công (`answer`, `tool_calls`, `grounded`...) thay vì để exception rơi ra ngoài — nhờ vậy 1 level bị lỗi (quota API, provider chết) không bao giờ làm sập cả menu CLI hay cả server web, đúng yêu cầu bắt buộc của đề bài.
  - Khi nối frontend, tôi phát hiện và sửa 1 bug encoding: `input()` trong `app.py` chỉ hoạt động đúng với tiếng Việt sau khi tôi reconfigure **cả `sys.stdin` lẫn `sys.stdout`** sang UTF-8 — ban đầu chỉ làm `stdout` nên câu hỏi nhập vào bị hiển thị mojibake dù câu trả lời LLM vẫn đúng.

- **Documentation**: `server.py` cố tình **không** import trực tiếp `handle_query_*` — mà import `call_level` và `LEVEL_LABELS` từ chính `app.py`, để đảm bảo CLI và Web luôn xử lý lỗi và định dạng kết quả giống hệt nhau, tránh lệch hành vi giữa 2 giao diện.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Trong lúc vận hành `src/server.py` để demo trên web, tôi liên tục đổi `GEMINI_API_KEY` trong `.env` và "restart" server bằng `pkill -f "src.server"` rồi chạy lại. Hiện tượng lạ: cùng 1 key, có lúc gọi được, có lúc báo lỗi xác thực — dù vừa test key đó thành công bằng script riêng.
- **Log Source**: Kết quả `netstat -ano | grep ":5000"` khi soát lại:
  ```
  TCP 127.0.0.1:5000  LISTENING  10700
  TCP 127.0.0.1:5000  LISTENING  20320
  TCP 127.0.0.1:5000  LISTENING  23988
  TCP 127.0.0.1:5000  LISTENING  27248
  TCP 127.0.0.1:5000  LISTENING  15032
  TCP 127.0.0.1:5000  LISTENING  13212
  TCP 127.0.0.1:5000  LISTENING  18608
  TCP 127.0.0.1:5000  LISTENING   6100
  ```
- **Diagnosis**: Không phải lỗi Agent/Prompt/Tool — mà là lỗi vận hành (Ops). `pkill -f "src.server"` chạy trong Git Bash trên Windows **không thực sự kill được tiến trình `python.exe`** của Windows, nên mỗi lần "restart" chỉ **cộng dồn thêm 1 server mới** chứ không thay server cũ. Kết quả: **8 process Flask cùng lắng nghe port 5000**. Mỗi request gửi tới `http://127.0.0.1:5000` bị hệ điều hành route ngẫu nhiên vào 1 trong 8 process đó — process nào còn giữ `GEMINI_API_KEY` cũ (đã hết hạn/hỏng) trong bộ nhớ thì báo lỗi, process nào có key mới nhất thì chạy đúng. Đây chính là lý do gây ra cảm giác "cùng 1 key lúc được lúc không".
- **Solution**: Lấy đúng PID Windows từ `netstat -ano`, kill triệt để bằng `taskkill //F //PID <pid>` cho cả 8 process (thay vì dựa vào `pkill` không đáng tin cậy trên môi trường lai Git-Bash/Windows này), xác nhận lại `netstat` chỉ còn đúng 1 dòng `LISTENING`, sau đó khởi động lại **đúng 1 server**. Test lại 4 lần liên tiếp cùng 1 key — cả 4 lần đều thành công, xác nhận hết flaky.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Khối `Thought` cho phép Agent tự quyết định *cần* dữ liệu gì trước khi trả lời, và quan trọng hơn — tự nhận ra khi nào **1 tool là đủ** (ví dụ Agent thường chỉ gọi `check_return_eligibility` mà bỏ qua `lookup_order`, vì nhận ra tool kia đã bao gồm sẵn bước tra đơn). Chatbot baseline không có bước suy luận trung gian này — nó chỉ có đúng 1 lượt sinh text, nên với cùng câu hỏi về đơn `#A1001`, nó buộc phải đưa ra ước lượng chung chung ("thường 3–7 ngày") thay vì con số thật (18 ngày đã qua, còn 12 ngày).
2. **Reliability**: Agent thực sự **tệ hơn** Chatbot trong đúng 1 tình huống tôi quan sát được: khi 1–2 bước đầu bị lỗi provider tạm thời (Gemini 503/429) tiêu tốn hết ngân sách `MAX_ITERATIONS`, Agent **đã tra được dữ liệu grounded đúng ở bước cuối** nhưng không còn bước nào để tổng hợp câu trả lời — kết quả cuối bị Guardrail ghi đè thành fallback chung chung, mất luôn cả câu trả lời đúng vừa có trong tay. Chatbot (chỉ 1 lượt gọi) không có kiểu lỗi nhiều bước này — nó hoặc trả lời được, hoặc lỗi hẳn, không bao giờ "có dữ liệu đúng nhưng không kịp nói ra". Ngoài ra, vì cần nhiều lượt gọi LLM hơn, Agent cũng **dễ dính lỗi quota API hơn Chatbot theo tỷ lệ** khi hạ tầng không ổn định.
3. **Observation**: Trong trace thật của câu `"#A1001"`, Observation ở bước 1 (*"Đơn hàng A1001... ĐỦ ĐIỀU KIỆN đổi trả. Đã qua 18 ngày... còn lại 12 ngày"*) được chèn nguyên văn vào `scratchpad` và gửi lại cho LLM — Thought ở bước 2 chỉ đơn giản là *"Tôi đã có đủ thông tin để trả lời"*, và Final Answer trích lại đúng các con số 18/12 ngày từ Observation, không thêm bớt. Điều này cho thấy environment feedback không chỉ "cung cấp thông tin" mà còn **định hình trực tiếp nội dung câu trả lời cuối** — khác hẳn Chatbot, nơi không có vòng phản hồi nào giữa các bước.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Hiện `src/server.py` chạy Flask dev server với 1 provider instance dùng chung toàn cục — cần chuyển sang WSGI server thật (gunicorn/waitress) và cân nhắc hàng đợi bất đồng bộ cho tool call nếu có nhiều người dùng đồng thời.
- **Safety**: Ưu tiên số 1 là sửa lỗi Guardrail nêu ở mục III.2 — tách riêng "bước lỗi do provider" khỏi ngân sách `MAX_ITERATIONS` dành cho bước suy luận thật, để không bao giờ đánh mất một Observation grounded hợp lệ đã có trong tay. Xa hơn, có thể thêm 1 lớp kiểm tra tự động so khớp tool Agent thực sự gọi với `required_tools`/`forbidden_tools` định nghĩa sẵn cho từng test case (đã bàn nhưng chưa implement) — giống vai trò một "Supervisor" nhẹ kiểm tra tool selection thay vì chỉ dựa vào đọc trace bằng mắt.
- **Performance**: `app.py`/`server.py` hiện tạo `provider` 1 lần rồi dùng chung cho mọi request (đúng hướng), nhưng chưa có cache cho câu hỏi lặp lại — nếu nhiều người demo cùng hỏi các câu mẫu trong `test_cases.json`, có thể cache kết quả theo `(level, question)` để giảm số lần gọi LLM thật, đỡ tốn quota vốn đã rất hạn chế ở free-tier.

---
