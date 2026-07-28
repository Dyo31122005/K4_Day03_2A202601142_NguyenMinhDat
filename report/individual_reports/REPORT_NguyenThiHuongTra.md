# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thị Hương Trà
- **Student ID**: [Điền MSSV]
- **Date**: 28/07/2026
- **Role**: Guardrails, Agent V2 & Defense (Cross-Audit)
---

## I. Technical Contribution (15 Points)

- **Modules Implementated**:
  - Bộ 6 câu hỏi bẫy (adversarial test) nhắm vào 6 loại lỗi khác nhau của Level 3: thiếu order_id, 2 order_id trong 1 câu, order_id viết thường, câu hỏi ngoài phạm vi tool (đổi màu ≠ đổi trả), không có order_id, order_id dính liền không tách được.
  - Fix 1 dòng trong `src/data/mock_db.py::find_order_by_id()` (chuẩn hóa `.strip().upper()`).
  - **TC06** (regression test) trong `config/test_cases.json`, tái hiện đúng lỗi đã tìm được để đảm bảo không tái phát.

- **Code Highlights**: Trong 6 câu bẫy, tôi phát hiện 1 bug thật (case-sensitivity, xem mục II) và xác nhận 2 câu **PASS** không cần sửa gì: câu *"Đổi trả giúp tôi cái đơn hàng gần nhất"* (Agent hỏi lại mã đơn, không tự bịa order_id) và câu *"Đơn A1001 và A1004, đơn nào đổi được?"* (Agent gọi `check_return_eligibility` cho **cả 2** đơn tuần tự rồi tổng hợp đúng — `tool_calls=2`, không dừng sau đơn đầu tiên như tôi lo ngại ban đầu).

- **Documentation**: Ghi lại đầy đủ vào `docs/trace_eval.md` mục "Failed Trace" — copy nguyên văn query gốc, trace từng step, answer cuối, và `tool_calls`/`steps_used`/`max_steps_reached`/`grounded` cho case thất bại, theo đúng quy trình RCA 5 bước (input → raw output → phân loại nhóm lỗi → fix tối thiểu → regression test).

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Câu bẫy `"đơn a1001"` (viết thường, không dấu `#`) — nhắm vào giả thuyết "regex trích order_id có case-sensitive/format-sensitive không?". Agent trích đúng order_id và gọi đúng tool `lookup_order[a1001]`, nhưng nhận lại `"LỖI: Không tìm thấy đơn hàng 'a1001' trong hệ thống"` — trong khi đơn `A1001` (viết hoa) chắc chắn tồn tại, đã được xác nhận đủ điều kiện đổi trả ở TC02.
- **Log Source**: Trace thật copy nguyên văn từ console:
  ```
  --- Step 1 ---
  Thought: Người dùng muốn tra cứu thông tin về đơn hàng a1001. Tôi sẽ sử dụng công cụ lookup_order để kiểm tra.
  Action: lookup_order[a1001]
  Observation: LỖI: Không tìm thấy đơn hàng 'a1001' trong hệ thống.
  ```
  (2 step sau đó dính lỗi quota Gemini `429`, không liên quan đến bug này — đã ghi chú rõ trong `trace_eval.md` để không đánh đồng 2 nguyên nhân khác nhau.)
- **Diagnosis** (theo đúng quy trình 5 bước):
  1. Input chính xác: `"đơn a1001"`.
  2. Raw trace: như trên, không diễn giải thêm.
  3. Nhóm lỗi: **Tool**, không phải Parser/Prompt — Agent hiểu đúng ý và gọi đúng tool tên, đúng tham số. Dòng gây lỗi: `src/data/mock_db.py::find_order_by_id()`, phép so sánh `order["order_id"] == order_id` không chuẩn hóa hoa/thường trước khi so khớp với `ORDERS` (lưu dạng chữ hoa).
  4. Fix tối thiểu — chỉ sửa đúng hàm này, không đụng file khác:
     ```python
     normalized_id = order_id.strip().upper()
     for order in ORDERS:
         if order["order_id"] == normalized_id:
             return order
     ```
  5. Regression test: thêm **TC06** (`"đơn a1001"`) vào `config/test_cases.json`.
- **Solution**: Sau khi fix, xác nhận lại ở cả 2 mức: (a) unit-level không cần LLM — `find_order_by_id('a1001')` trả đúng order dict, `find_order_by_id('Z9999')` vẫn trả `None` (không phá hành vi "not found" thật); (b) qua tool — `check_return_eligibility('a1001')` trả đúng *"ĐỦ ĐIỀU KIỆN đổi trả... còn lại 12 ngày"*.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Vai trò tấn công/phòng thủ cho tôi thấy rõ nhất giá trị của `Thought`: trong câu 2-order-id, Agent **tự chia nhỏ** thành 2 lượt gọi tool tuần tự thay vì bối rối hay chỉ xử lý 1 đơn — một hành vi suy luận đa bước mà Chatbot (1 lượt gọi duy nhất) không thể tái hiện được.
2. **Reliability**: Khi tấn công bằng câu hỏi ngoài phạm vi tool ("đổi màu khác" — không phải "đổi trả"), Agent vẫn chọn `check_return_eligibility` như một proxy hợp lý, nhưng đây là điểm cần cảnh giác: Agent có thể trả lời "đủ điều kiện đổi trả" mà không làm rõ nó **không thể xử lý yêu cầu đổi màu** cụ thể — một dạng overreach tinh vi cần thêm câu bẫy để kiểm chứng kỹ hơn (chưa kết luận được hoàn toàn do hết quota API giữa lúc test).
3. **Observation**: Bug case-sensitivity chứng minh Observation **chỉ tốt bằng chính Tool sinh ra nó** — Agent suy luận hoàn toàn đúng, Parser hoàn toàn đúng, nhưng Observation sai khiến cả chuỗi suy luận đi theo hướng sai. Vai trò Defense vì vậy không chỉ kiểm tra Agent mà phải kiểm tra cả tầng Tool/Data đứng sau nó.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Hoàn thành 3 câu bẫy còn dang dở (đổi màu, không có order_id, order_id dính liền) khi có quota API ổn định, để có bộ regression đầy đủ 9 case thay vì 6.
- **Safety**: Thêm 1 "Supervisor" nhẹ kiểm tra Agent không tự ý gọi `create_return_request` (tool duy nhất có side effect) khi người dùng chưa xác nhận muốn đổi trả — hiện chưa có câu bẫy nào kiểm tra riêng rủi ro này.
- **Performance**: Ghi nhận thêm số lần Parser error do lỗi provider tạm thời (503/429) tách biệt với Parser error do LLM sinh sai định dạng thật — hiện 2 loại đang bị gộp chung khiến khó đo chính xác tỷ lệ lỗi Parser thật của Agent.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
