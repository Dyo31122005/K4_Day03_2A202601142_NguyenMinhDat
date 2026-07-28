# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trần Hoàng Mai Anh
- **Student ID**: 2A202601324
- **Date**: 28/07/2026
- **Role**: Tool & Prompt Engineer (Role 2 + Role 3)
---

## I. Technical Contribution (15 Points)

- **Modules Implementated**:
  - `src/tools.py` — viết 3 tool cho đề tài Đơn hàng/Đổi trả: `lookup_order(order_id)`, `check_return_eligibility(order_id)`, `create_return_request(order_id, reason)`. Mỗi tool có đủ 8 mục của Tool Contract (Purpose, Input/Output schema, Error semantics, Side effect, Example, Safety).
  - `src/prompts.py` — viết `CHATBOT_BASELINE_PROMPT` (1 LLM call, không tool) và `REACT_SYSTEM_PROMPT` (liệt kê đúng 3 tool, ép định dạng `Thought → Action → Final Answer`, cấu hình Guardrail `MAX_ITERATIONS = 3`).

- **Code Highlights**: Điểm tôi chú trọng nhất là đảm bảo **contract của tool khớp 100% với mô tả trong prompt** — vd `check_return_eligibility` được mô tả trong `REACT_SYSTEM_PROMPT` là *"Kiểm tra một đơn hàng còn trong hạn đổi trả hay không"*, và docstring của hàm cũng nêu rõ *"tự tra thêm sản phẩm + chính sách theo category"* — để LLM hiểu đúng nó không cần gọi thêm `lookup_order` riêng. Ngoài ra, mọi tool đều **không bao giờ raise exception** — mọi lỗi (không tìm thấy đơn, lỗi hệ thống) được bắt bằng try/except và trả về string tiền tố `"LỖI:"`, để Agent đọc được như Observation bình thường thay vì làm crash vòng lặp.

- **Documentation**: Đã thêm vào `REACT_SYSTEM_PROMPT` đoạn quy tắc an toàn bắt buộc: *"Nếu Observation trả về là một lỗi (bắt đầu bằng 'LỖI:', 'Tool error:' hoặc 'Parser error:'), hãy thông báo trung thực lỗi đó... TUYỆT ĐỐI KHÔNG được tự suy diễn, đoán mò hay bịa ra dữ liệu."* — đây là điều kiện tiên quyết để Agent vượt qua các câu bẫy hallucination.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Khi tiếp nhận `src/prompts.py` từ bản boilerplate gốc của repo (trước khi đề tài chốt sang Đơn hàng/Đổi trả), tôi phát hiện `REACT_SYSTEM_PROMPT` **vẫn liệt kê 2 tool của đề tài mẫu cũ**: `get_weather[location]` và `search_flights[origin, destination]` — hai tool này **không hề tồn tại** trong `src/tools.py` của đề tài hiện tại.
- **Log Source**: Nội dung `REACT_SYSTEM_PROMPT` trước khi sửa (trích từ git history của file):
  ```
  Danh sách các công cụ bạn có thể sử dụng:
  1. get_weather[location]: Tra cứu thời tiết hiện tại của một thành phố.
  2. search_flights[origin, destination]: Tra cứu chuyến bay giữa 2 địa điểm.
  ```
- **Diagnosis**: Đây là lỗi **Prompt/Tool contract mismatch** — nếu không phát hiện trước khi Level 3 chạy thật, Agent sẽ đọc system prompt và có thể tự tin sinh ra `Action: get_weather[...]` cho câu hỏi về đơn hàng (vì đó là tool duy nhất nó "biết"), rồi bị `AVAILABLE_TOOLS` từ chối với lỗi `"Tool 'get_weather' không tồn tại"` — một lỗi hoàn toàn có thể tránh được nếu prompt được đồng bộ với tool registry ngay từ đầu, thay vì phát hiện lúc chạy.
- **Solution**: Viết lại toàn bộ danh sách tool trong `REACT_SYSTEM_PROMPT` khớp đúng 3 hàm thật trong `tools.AVAILABLE_TOOLS`, đồng thời rà lại toàn bộ prompt để đảm bảo không còn tham chiếu nào tới domain cũ (thời tiết/vé máy bay). Sau khi sửa, chạy `python -m src.ai_levels.level3_reactive_agent` xác nhận Agent gọi đúng `check_return_eligibility`/`lookup_order`, không còn cố gọi tool ảo nào nữa.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Việc viết `REACT_SYSTEM_PROMPT` dạy tôi rằng chất lượng `Thought` của Agent phụ thuộc trực tiếp vào **độ rõ ràng của mô tả tool** — mô tả mơ hồ dẫn đến Agent chọn sai tool hoặc gọi thừa; mô tả quá chi tiết (như nêu rõ `check_return_eligibility` đã bao gồm tra đơn) giúp Agent tối ưu số bước.
2. **Reliability**: Chatbot (không cần tool) miễn nhiễm với loại lỗi "prompt liệt kê sai tool" — vì nó không có khái niệm tool nào cả. Đây là 1 điểm Chatbot "an toàn hơn" xét thuần về mặt vận hành, dù nó không giải quyết được nhu cầu thật của người dùng.
3. **Observation**: Tôi nhận ra Observation không chỉ là "kết quả tool" mà còn phải **được thiết kế để LLM đọc hiểu được ngay** — vd `check_return_eligibility` trả về câu văn hoàn chỉnh ("ĐỦ ĐIỀU KIỆN đổi trả... còn lại 12 ngày...") thay vì trả về dict thô, để Agent có thể trích thẳng vào Final Answer mà không cần diễn giải thêm.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Nếu thêm tool mới, cần một quy trình kiểm tra tự động "prompt tool list ⊆ AVAILABLE_TOOLS ⊆ prompt tool list" (đối chiếu 2 chiều) để không lặp lại lỗi mismatch đã gặp.
- **Safety**: Viết thêm test case buộc Agent gặp tình huống cần gọi `create_return_request` (tool duy nhất có side effect) để kiểm tra Agent có tự ý tạo yêu cầu đổi trả khi người dùng chỉ hỏi "có đổi được không" hay không (rủi ro overreach).
- **Performance**: Cân nhắc rút gọn văn phong mô tả tool trong prompt (hiện khá dài) để giảm token mỗi lượt gọi, mà vẫn giữ đủ thông tin để Agent không gọi sai/thừa tool.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
