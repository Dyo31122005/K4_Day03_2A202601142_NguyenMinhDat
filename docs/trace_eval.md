# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*
*Đề tài: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Cần suy luận từ tra đơn hàng (`lookup_order`) đến tính hạn đổi trả dựa trên category + ngày mua (`check_return_eligibility`), rồi mới kết luận. |
| 🛠️ **Tool Interaction** | `5/5` | Bắt buộc phải tra dữ liệu thật qua `mock_db.py` (đơn hàng, sản phẩm, chính sách) — không thể trả lời chính xác chỉ bằng kiến thức tĩnh của LLM. |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả tool quyết định nhánh trả lời tiếp theo: đơn `delivered` mới tính hạn; đơn `shipping`/`cancelled` dừng sớm; đơn không tồn tại phải báo lỗi trung thực chứ không suy diễn tiếp. |
| ⏳ **Long Horizon** | `3/5` | Đa số case chỉ cần 1-2 bước tool (thường `check_return_eligibility` đã gộp sẵn tra đơn + tra chính sách trong 1 lần gọi); trường hợp nhiều order_id trong 1 câu mới cần lặp 2 vòng. |
| **TỔNG ĐIỂM FIT** | **16/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT** — Chatbot thuần không có cách nào biết ngày mua/trạng thái đơn thật, buộc phải từ chối hoặc đoán số liệu chung chung không khớp chính sách thật. |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #2 — `"Đơn hàng #A1001 của tôi có đổi trả được không?"`)

### 🤖 Chatbot Baseline (Level 2):
* **Phản hồi**: *"...vì tôi là chatbot tư vấn chung và không có kết nối trực tiếp với hệ thống dữ liệu đơn hàng theo thời gian thực, nên tôi không thể tra cứu tình trạng chi tiết của mã đơn hàng #A1001... Tuy nhiên, thông thường để một đơn hàng có thể đổi trả, bạn có thể xem qua một số điều kiện chung: Thời hạn đổi trả thường 3-7 ngày, hoặc lên tới 30 ngày tùy chính sách riêng..."*
* **Nhận xét**: An toàn (không bịa cụ thể ngày mua/trạng thái đơn), nhưng số liệu "thường 3-7 ngày" đưa ra **không khớp với chính sách thật** (`mock_db.RETURN_POLICY`: quần áo 30 ngày, điện tử chỉ 7 ngày, không có mốc "3-7 ngày" nào) — nghe hợp lý nhưng không có căn cứ (`tool_calls=0`, `grounded=False`).

### 🧠 ReAct Agent (Level 3):
```
Thought: Người dùng muốn biết đơn hàng #A1001 có thể đổi trả được hay không.
         Tôi cần kiểm tra điều kiện đổi trả của đơn hàng này bằng công cụ
         check_return_eligibility.
Action: check_return_eligibility[A1001]
Observation: Đơn hàng A1001 (Áo thun cotton unisex) ĐỦ ĐIỀU KIỆN đổi trả.
             Đã qua 18 ngày kể từ ngày mua, còn trong hạn 30 ngày (còn lại
             12 ngày). Điều kiện: còn tem, chưa qua sử dụng.
Thought: Tôi đã có đủ thông tin để trả lời.
Final Answer: Đơn hàng #A1001 (Áo thun cotton unisex) của bạn ĐỦ ĐIỀU KIỆN
              đổi trả. Đã qua 18 ngày kể từ ngày mua, bạn vẫn còn 12 ngày
              để thực hiện đổi trả (trong chính sách 30 ngày)...
```
* **Nhận xét**: Grounded 100% — mọi con số trong Final Answer (18 ngày, 12 ngày, 30 ngày) đều trích thẳng từ Observation thật, không suy diễn thêm. `tool_calls=1`, `grounded=True`. Đáng chú ý: Agent tự nhận ra `check_return_eligibility` đã bao gồm sẵn bước tra đơn hàng, nên không cần gọi thêm `lookup_order` riêng — tiết kiệm 1 bước so với dự tính ban đầu.

---

## 📐 3. RUBRIC ĐÁNH GIÁ 0–2 ĐIỂM MỖI CASE

Chạy toàn bộ `config/test_cases.json` (TC01–TC06) qua cả Level 2 (Chatbot) và Level 3 (Agent), chấm theo 4 tiêu chí. Ghi chú: 2 tiêu chí **Grounding** và **Tool selection** không áp dụng được (N/A) cho các câu hỏi không cần tra dữ liệu thật (TC05) — chấm N/A thay vì ép về 0 để không đánh giá sai một hành vi đúng (không gọi tool khi không cần tool cũng là đúng).

| TC | Câu hỏi | Level | Factual correctness | Grounding | Tool selection | Termination | Tổng |
| :-: | :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| 01 | Chính sách đổi trả của cửa hàng là gì? | Chatbot | 1 | 0 | N/A | 2 | 3/6 |
| 01 | ″ | Agent | 1¹ | 0 | 0² | 2 | 3/8 |
| 02 | Đơn `#A1001` có đổi trả được không? | Chatbot | 1 | 0 | N/A | 2 | 3/6 |
| 02 | ″ | Agent | 2 | 2 | 2 | 2 | **8/8** |
| 03 | Đơn `#A1004` mua lâu rồi, đổi được không? | Chatbot | 1 | 0 | N/A | 2 | 3/6 |
| 03 | ″ | Agent | 2 | 2 | 2 | 2 | **8/8** |
| 04 | Đơn `#Z9999` giao trễ 2 tháng (bẫy — không tồn tại) | Chatbot | 1 | 0 | N/A | 2 | 3/6 |
| 04 | ″ | Agent | 2 | 2 | 2 | 2 | **8/8** |
| 05 | Bạn khỏe không? (chit-chat, không cần tool) | Chatbot | 2 | N/A | N/A | 2 | 4/4 |
| 05 | ″ | Agent | 2 | N/A | 2³ | 2 | 6/6 |
| 06 | "đơn a1001" (regression — trước fix) | Agent | **0** | 1⁴ | 2 | 2 | 5/8 |
| 06 | "đơn a1001" (regression — sau fix) | Agent | **2** | 2 | 2 | 2 | **8/8** |

¹ Agent trung thực từ chối vì không có tool tra chính sách chung — không sai, nhưng không giải quyết được yêu cầu.
² Không có tool nào trong `AVAILABLE_TOOLS` phù hợp câu hỏi chính sách chung (chỉ có tool theo từng đơn hàng cụ thể) — đây là **khoảng trống về phạm vi tool**, không phải Agent chọn sai; chấm 0 theo đúng câu chữ rubric (“Không gọi” = 0đ) nhưng bản chất khác với việc Agent nhầm lẫn.
³ Agent không gọi tool nào cho câu chit-chat — đúng theo tinh thần "đừng vội kết luận Agent luôn thắng" (CODELAB.md mục 2), không phải lỗi.
⁴ Trước khi fix, Observation *có tồn tại* (tool chạy không lỗi) nhưng **nội dung Observation sai** ("không tìm thấy" dù đơn có thật) — chấm 1 (bằng chứng thiếu chính xác) thay vì 2.

**Tổng kết**: Agent đạt **8/8 tuyệt đối** trên mọi câu hỏi thật sự cần tra dữ liệu (TC02, TC03, TC04, và TC06 sau fix) — bao gồm cả câu bẫy hallucination (TC04). Chatbot chỉ đạt **3/6** đều đặn trên các câu này vì cấu trúc `grounding=0` không thể tránh khỏi. TC01 là điểm yếu chung của cả 2 level (thiếu tool tra chính sách tổng quát) — xem đề xuất ở mục 5.

---

## 🕳️ 4. FAILED TRACE — CÂU HỎI BẪY (Level 3 ReAct Agent)

Chạy 6 câu bẫy ngoài 5 test case chuẩn qua `handle_query_reactive_agent()` (model: `gemini-flash-latest`). Kết quả:

| Câu bẫy | Nhắm vào | Kết quả |
| :--- | :--- | :--- |
| "Đổi trả giúp tôi cái đơn hàng gần nhất" | Data/Parser — không có order_id | ✅ PASS — Agent hỏi lại mã đơn, không bịa order_id (`tool_calls=0`) |
| "Đơn A1001 và A1004, đơn nào đổi được?" | Loop — 2 order_id trong 1 câu | ✅ PASS — Agent gọi `check_return_eligibility` cho **cả 2** đơn tuần tự rồi tổng hợp đúng (`tool_calls=2`, `grounded=True`) |
| "đơn a1001" (thường, không dấu #) | Parser — case-sensitive? | ❌ **FAIL — xem chi tiết bên dưới** (đã fix, xem mục 3 TC06) |
| "Tôi muốn đổi đơn A1001 sang màu khác, được không?" | Tool/Prompt — ngoài phạm vi | ⚠️ Chưa kết luận được — Observation lấy đúng (`check_return_eligibility[A1001]` → đủ điều kiện), nhưng bị quota Gemini (429) chặn mất bước tổng hợp Final Answer nên chưa biết agent có phân biệt "đổi trả" ≠ "đổi màu" hay không. Cần chạy lại. |
| "Đơn hàng của tôi có đổi trả được không?" (không order_id) | Loop | ⚠️ Chưa kết luận — cả 3 step đều bị quota Gemini (429) chặn hoàn toàn, không có phản hồi LLM thật nào. Cần chạy lại. |
| "A1001A1002" (dính liền) | Parser — regex tách sai | ⚠️ Chưa kết luận — cả 3 step đều bị quota Gemini (429) chặn hoàn toàn. Cần chạy lại. |

### ❌ FAILED TRACE #1 — Case-sensitivity bug (order_id viết thường bị báo "không tìm thấy" dù đơn có thật)

**Query gốc**: `"đơn a1001"`

**Trace đầy đủ** (nguyên văn từ `handle_query_reactive_agent`):

```
--- Step 1 ---
Thought: Người dùng muốn tra cứu thông tin về đơn hàng a1001. Tôi sẽ sử dụng công cụ lookup_order để kiểm tra.
Action: lookup_order[a1001]
Observation: LỖI: Không tìm thấy đơn hàng 'a1001' trong hệ thống.

--- Step 2 ---
Thought: [Gemini Exception]: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https:/
Observation: Parser error: không thể hiểu định dạng action, vui lòng thử lại

--- Step 3 ---
Thought: [Gemini Exception]: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https:/
Observation: Parser error: không thể hiểu định dạng action, vui lòng thử lại
```

**Answer cuối cùng**: `"Xin lỗi, tôi cần thêm thông tin hoặc không thể hoàn tất yêu cầu này trong giới hạn xử lý, vui lòng liên hệ hỗ trợ trực tiếp."`

**Metrics**: `tool_calls=1` | `steps_used=3` | `max_steps_reached=True` | `grounded=True`

**Vì sao đây là lỗi thật (không phải do quota bước 2-3)**: Bug đã lộ rõ ngay ở **Step 1** — đơn hàng `A1001` **có tồn tại thật** trong `mock_db.ORDERS` (đã xác nhận đủ điều kiện đổi trả ở TC02 và BAY2), nhưng khi LLM trích đúng order_id từ câu hỏi và giữ nguyên chữ thường (`a1001`) làm tham số gọi `lookup_order[a1001]`, tool trả về **"Không tìm thấy đơn hàng 'a1001'"** — một **false negative**, không phải hallucination nhưng là kết luận sai sự thật. Quota 429 ở step 2-3 chỉ chặn mất bước LLM tổng hợp Final Answer, không liên quan đến lỗi này.

**Fix đã áp dụng**: `src/data/mock_db.py::find_order_by_id()` chuẩn hóa `order_id.strip().upper()` trước khi so khớp. Regression test **TC06** đã thêm vào `config/test_cases.json`, xác nhận PASS 8/8 sau fix (xem bảng mục 3).

---

## 5. Đề xuất cải thiện (rút ra từ toàn bộ quá trình đánh giá)

- **TC01 (chính sách chung) là điểm yếu chung của cả 2 level**: hiện `AVAILABLE_TOOLS` chỉ có tool theo từng đơn hàng cụ thể (`lookup_order`, `check_return_eligibility`, `create_return_request`), không có tool tra "chính sách chung theo category" — trong khi Level 1 (rule-based) lại xử lý được câu này (đọc thẳng `mock_db.RETURN_POLICY`). Nên bổ sung 1 tool `get_return_policy(category)` cho Level 3 để đồng bộ năng lực với Level 1.
- **Guardrail đôi khi ăn mất Observation grounded hợp lệ**: khi 1-2 bước đầu bị lỗi provider tạm thời (429/503) tiêu tốn hết `MAX_ITERATIONS`, Agent có thể đã tra đúng dữ liệu ở bước cuối nhưng không còn bước nào để tổng hợp Final Answer, kết quả bị ghi đè thành fallback chung chung dù có bằng chứng đúng trong tay.
