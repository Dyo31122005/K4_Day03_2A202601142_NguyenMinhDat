# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: A1
- **Team Members**: Nguyễn Minh Đạt, Hà Anh Tuấn, Trần Hoàng Mai Anh, Nguyễn Thị Hương Trà.
- **Deployment Date**: 2026-07-28

---

## 1. Executive Summary

Đề tài: **Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả** — agent trả lời câu hỏi về tình trạng đơn hàng và điều kiện đổi trả, dựa trên dữ liệu thật trong `src/data/mock_db.py` (12 đơn hàng, 4 category sản phẩm, chính sách đổi trả riêng từng category).

- **Success Rate**: Theo Rubric 0-2đ/tiêu chí (4 tiêu chí: Factual correctness, Grounding, Tool selection, Termination — chi tiết `docs/trace_eval.md` mục 3), **Agent đạt tuyệt đối 8/8 trên 4/6 test case** cần dữ liệu thật (TC02, TC03, TC04, và TC06 sau khi fix), trong khi **Chatbot chỉ đạt đều 3/6** trên cùng các case đó (luôn mất điểm Grounding vì `tool_calls=0` theo thiết kế). TC01 (chính sách chung) là điểm yếu chung của **cả 2 level** — cả Chatbot lẫn Agent đều không trả lời grounded được vì Agent chưa có tool tra chính sách tổng quát (xem mục 5). Trong 6 câu bẫy adversarial bổ sung ngoài bộ chuẩn, phát hiện và fix được 1 bug thật (case-sensitivity — nay đã PASS 8/8), 2 câu PASS rõ ràng, 3 câu chưa kết luận được do hết quota API giữa chừng.
- **Key Outcome**: Agent (Level 3) đạt **grounded=True cho 100% câu hỏi có order_id cụ thể**, nhờ gọi đúng tool `check_return_eligibility`/`lookup_order` và dùng thẳng Observation thật làm bằng chứng. Chatbot Baseline (Level 2) **luôn có `tool_calls=0`** theo thiết kế — khi bị hỏi về đơn hàng cụ thể, nó hoặc từ chối trung thực, hoặc đưa ra các con số "thường thấy" (ví dụ "3–7 ngày") **không khớp với chính sách thật** (quần áo 30 ngày, điện tử chỉ 7 ngày) — minh chứng rõ ràng cho luận điểm "Chatbot an toàn nhưng không giải quyết được nhu cầu thật, dễ tạo cảm giác đúng mà không có bằng chứng".

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Vì `src/providers.py` chỉ cung cấp `provider.generate(prompt, system_prompt)` dạng single-turn (không có function-calling có cấu trúc, không tự lưu lịch sử hội thoại), vòng lặp ReAct được cài theo kiểu **text-based**:

```
1. scratchpad = "" (rỗng)
2. Lặp tối đa MAX_ITERATIONS = 3 lần:
   a. prompt = user_query + scratchpad (toàn bộ lịch sử Thought/Action/Observation trước đó)
   b. Gọi LLM(prompt, system_prompt=REACT_SYSTEM_PROMPT) -> raw_text
   c. CẮT bỏ mọi nội dung sau nhãn "Observation:" trong raw_text
      (đề phòng LLM tự bịa luôn Observation giả — Observation CHỈ được
      phép do code tạo ra từ tool thật, không bao giờ do LLM tự viết)
   d. Parse phần còn lại bằng regex: có "Final Answer:" -> dừng, trả lời.
      Có "Action: tool[args]" -> gọi tool thật, chèn Observation thật vào
      scratchpad, tăng step, lặp tiếp.
      Không parse được gì -> "Parser error: ..." làm Observation, agent
      vẫn được tiếp tục lặp (không dừng ngay, trừ khi hết MAX_ITERATIONS).
3. Hết MAX_ITERATIONS mà chưa có Final Answer -> safe fallback:
   "Xin lỗi, tôi cần thêm thông tin hoặc không thể hoàn tất yêu cầu này
   trong giới hạn xử lý, vui lòng liên hệ hỗ trợ trực tiếp."
```

Mọi tool chỉ được gọi nếu tên nằm trong whitelist `tools.AVAILABLE_TOOLS`; tool lỗi/raise exception được bắt bằng try/except và biến thành Observation dạng `"Tool error: ..."`, không bao giờ crash vòng lặp.

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `lookup_order` | `order_id: str` | Tra cứu thông tin thô 1 đơn hàng (ngày đặt, số lượng, tổng tiền, trạng thái). |
| `check_return_eligibility` | `order_id: str` | Kết luận đơn hàng có đủ điều kiện đổi trả không — tự tra thêm sản phẩm + chính sách theo category, tính số ngày còn hạn/vượt hạn. |
| `create_return_request` | `order_id: str, reason: str` | Tạo yêu cầu đổi trả chính thức — **tool duy nhất có side effect** (ghi thêm record vào `mock_db.RETURN_REQUESTS`). |

Cả 3 tool wrap qua các hàm gốc trong `src/data/mock_db.py` (`find_order_by_id`, `find_product_by_id`, `find_policy_by_category`, `append_return_request`) và luôn trả về string, không bao giờ để exception lọt ra ngoài.

### 2.3 LLM Providers Used

- **Primary**: Google Gemini — model `gemini-flash-latest` qua SDK `google-genai`.
- **Secondary (Backup)**: `src/providers.py` là adapter đa nhà cung cấp — hỗ trợ sẵn OpenAI, Anthropic, OpenRouter, chỉ cần đổi biến môi trường `LLM_PROVIDER`. Chưa thực sự chạy test trên các provider này trong đợt đánh giá này (chỉ dùng Gemini), nhưng kiến trúc đã sẵn sàng chuyển đổi khi Gemini gặp sự cố (xem mục 6).

---

## 3. Telemetry & Performance Dashboard

- **Số bước LLM trung bình cho câu hỏi grounded thành công**: 2 bước (1 bước gọi tool + 1 bước tổng hợp Final Answer). Guardrail `MAX_ITERATIONS = 3`.
- **Tool calls trung bình/câu hỏi**:
  - Level 1 (rule-based): 3 (câu hỏi đổi trả — `find_order_by_id` + `find_product_by_id` + `find_policy_by_category`) hoặc 4 (câu hỏi chính sách chung — lặp qua từng category).
  - Level 3 (ReAct Agent): thường chỉ **1** — LLM tự nhận ra `check_return_eligibility` đã bao gồm luôn bước tra đơn, không cần gọi `lookup_order` riêng (hành vi tối ưu quan sát được nhiều lần, không phải lỗi).
- **Giới hạn hạ tầng thực tế (đáng ghi nhận thay cho latency benchmark)**: Gemini free-tier quota rất thấp — quan sát thấy lỗi `429 RESOURCE_EXHAUSTED` xuất hiện chỉ sau **~10–20 request** trong một phiên test dồn dập. Đây là nút thắt cổ chai vận hành thật, ảnh hưởng trực tiếp đến khả năng chạy full bộ test case liên tục (xem mục 6).
- **Chi phí**: $0 (dùng Gemini free tier trong suốt quá trình phát triển và test).

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: Case-Sensitivity False Negative (Tool layer)

- **Input**: `"đơn a1001"` (order_id viết thường, không có dấu `#`)
- **Trace quan sát được**:
  ```
  Thought: Người dùng muốn tra cứu thông tin về đơn hàng a1001...
  Action: lookup_order[a1001]
  Observation: LỖI: Không tìm thấy đơn hàng 'a1001' trong hệ thống.
  ```
- **Root Cause**: LLM trích đúng order_id và gọi đúng tool (không phải lỗi Parser/Prompt) — nhưng `find_order_by_id()` trong `src/data/mock_db.py` so khớp **case-sensitive tuyệt đối** (`order["order_id"] == order_id`), trong khi `ORDERS` lưu order_id dạng chữ hoa (`"A1001"`). Đây là **false negative ở tầng Tool/Data**: đơn hàng có tồn tại thật nhưng bị báo sai là "không tìm thấy".
- **Fix đã áp dụng** (chỉ sửa đúng 1 hàm, không sửa gì khác):
  ```python
  def find_order_by_id(order_id: str) -> dict | None:
      normalized_id = order_id.strip().upper()
      for order in ORDERS:
          if order["order_id"] == normalized_id:
              return order
      return None
  ```
- **Regression test**: đã thêm **TC06** vào `config/test_cases.json` (`"đơn a1001"`, kỳ vọng tìm thấy A1001 đủ điều kiện đổi trả). Đã xác nhận fix đúng ở cả mức unit (`find_order_by_id('a1001')` → trả đúng order dict) lẫn qua tool `check_return_eligibility('a1001')` → *"ĐỦ ĐIỀU KIỆN đổi trả... còn lại 12 ngày"*, không phá vỡ hành vi "not found" thật cho `Z9999`.

### Case Study 2 (Bonus): Guardrail nuốt mất Observation grounded hợp lệ

- **Quan sát**: Khi 1–2 bước đầu của vòng lặp bị lỗi provider (vd Gemini 503/429, được xử lý như `Parser error` để agent còn cơ hội thử lại), và bước cuối cùng (đúng lúc chạm `MAX_ITERATIONS`) mới thực sự gọi tool thành công và nhận Observation đúng — agent **không còn bước nào để tổng hợp Final Answer** từ Observation đó. Kết quả cuối bị Guardrail ghi đè thành safe-fallback chung chung, dù dữ liệu grounded thật đã có trong tay.
- **Root Cause**: Guardrail đếm **mọi bước như nhau** (kể cả bước thất bại do lỗi provider tạm thời) vào cùng ngân sách `MAX_ITERATIONS` với bước suy luận thật — không phân biệt "lỗi hạ tầng ngoài ý muốn" với "bước suy luận hợp lệ".
- **Đề xuất fix** (chưa áp dụng, để nhóm cân nhắc): không tính các bước lỗi do provider (không phải do Agent/Tool) vào ngân sách `MAX_ITERATIONS`, hoặc thêm bước tổng hợp câu trả lời trực tiếp từ Observation hợp lệ cuối cùng trước khi kích hoạt fallback.

---

## 5. Ablation Studies & Experiments

### Experiment 1: `REACT_SYSTEM_PROMPT` v1 vs v2

- **Diff**: Bản v1 (boilerplate gốc) liệt kê sai tool (`get_weather`, `search_flights` từ đề tài mẫu cũ) và **không có** chỉ dẫn về cách xử lý khi Observation là lỗi. Bản v2 sửa đúng 3 tool thật của đề tài, và thêm đoạn:
  > *"Nếu Observation trả về là một lỗi (bắt đầu bằng "LỖI:", "Tool error:" hoặc "Parser error:"), hãy thông báo trung thực lỗi đó cho người dùng. TUYỆT ĐỐI KHÔNG được tự suy diễn, đoán mò hay bịa ra dữ liệu... Chỉ được dùng đúng dữ liệu có trong các Observation đã nhận để trả lời."*
- **Result**: Không đo bằng % định lượng chính thức (chưa chạy A/B có kiểm soát), nhưng **về mặt định tính**: đây là điều kiện tiên quyết để agent vượt qua TC04/TC06 (câu bẫy đơn không tồn tại / case-sensitivity) — không có đoạn này, không có gì ràng buộc agent phải trung thực khi tool báo lỗi.

### Experiment 2: Chatbot (Level 2) vs Agent (Level 3)

| Case | Chatbot Result (điểm/8) | Agent Result (điểm/8) | Winner |
| :--- | :--- | :--- | :--- |
| TC01 – Chính sách đổi trả chung | Đưa số liệu chung không khớp thật (3/6) | Từ chối trung thực — chưa có tool phù hợp (3/8) | **Draw (cả 2 đều yếu)** |
| TC02 – "#A1001 đổi trả được không?" | Từ chối tra cứu cụ thể, đưa số liệu "thường 3–7 ngày" **không khớp chính sách thật** (3/6) | **"ĐỦ ĐIỀU KIỆN, còn 12 ngày"** — grounded đúng (**8/8**) | **Agent** |
| TC03 – "#A1004 mua lâu rồi" | Ước lượng chung chung, không xác nhận được (3/6) | **"ĐÃ HẾT HẠN, vượt hạn 80 ngày"** — grounded đúng (**8/8**) | **Agent** |
| TC04 – "#Z9999 giao trễ 2 tháng" (bẫy) | Từ chối lịch sự, không xác nhận đơn có tồn tại hay không (3/6) | **"Không tìm thấy đơn hàng Z9999"** — grounded, không hallucinate (**8/8**) | **Agent** |
| TC05 – "Bạn khỏe không?" | Đúng, trả lời tự nhiên (4/4) | Đúng, trả lời tự nhiên, không gọi tool thừa (6/6) | Draw |
| TC06 – "đơn a1001" (regression) | *(không test — câu chỉ có ý nghĩa với Agent)* | Trước fix: 5/8 (Factual=0, false negative) → Sau fix: **8/8** | **Agent (sau fix)** |

*Bảng chấm chi tiết theo từng tiêu chí (Factual/Grounding/Tool selection/Termination): xem `docs/trace_eval.md` mục 3.*

### Hybrid Decision Flowchart

Sơ đồ định tuyến Chatbot path vs ReAct Agent path — xem `docs/hybrid_flowchart.mermaid`. Logic chính: câu hỏi có nhắc `order_id` cụ thể hoặc cần dữ liệu thời gian thực của 1 đơn → đi ReAct Agent path (gọi tool thật); câu hỏi lý thuyết chung/chit-chat không cần bằng chứng → đi Chatbot path (nhanh, rẻ hơn). Nhánh Guardrail (`MAX_ITERATIONS`) được vẽ tách riêng vì áp dụng xuyên suốt mọi luồng đi qua Agent path.

---

## 6. Production Readiness Review

- **Coverage gap (mới phát hiện qua Rubric mục 5/Experiment 2)**: `AVAILABLE_TOOLS` hiện chỉ có tool theo từng đơn hàng cụ thể, **không có tool tra "chính sách chung theo category"** — khiến TC01 là điểm yếu của cả Agent lẫn Chatbot (cả 2 đều không grounded được). Đề xuất: thêm tool `get_return_policy(category)` wrap `mock_db.find_policy_by_category`, để Agent đạt năng lực tương đương Level 1 (vốn đã xử lý được câu này bằng cách đọc thẳng `mock_db.RETURN_POLICY`).
- **Security**: Input `order_id`/`reason` hiện chỉ được parse bằng regex, chưa có tầng validate/sanitize riêng trước khi đưa vào tool. Frontend web (`front_end/code.html`) đã có escape HTML cơ bản khi render câu trả lời động (chống XSS), nhưng API `/api/query` trong `src/server.py` **chưa có auth hay rate-limit** — phù hợp cho demo cục bộ, chưa sẵn sàng expose ra internet.
- **Guardrails**: `MAX_ITERATIONS = 3` chặn lặp vô hạn; whitelist `AVAILABLE_TOOLS` chặn agent gọi tool tùy tiện ngoài 3 tool đã khai báo. Điểm còn thiếu: xem Case Study 2 ở mục 4 (guardrail chưa phân biệt lỗi hạ tầng với bước suy luận thật).
- **Scaling**: `src/server.py` hiện chạy bằng Flask dev server (tự cảnh báo "not for production"), dùng 1 instance provider toàn cục. Cần WSGI server thật (gunicorn/waitress) nếu nhiều người dùng đồng thời. **Vấn đề vận hành thực tế nghiêm trọng nhất đã gặp**: quota Gemini free-tier cạn rất nhanh (~10–20 request là bắt đầu `429`), từng khiến nhiều lần test bị gián đoạn giữa chừng — trước khi lên production cần nâng cấp gói trả phí hoặc kích hoạt fallback sang provider khác (OpenAI/Anthropic) đã có sẵn kiến trúc trong `providers.py` nhưng chưa được tự động hoá (hiện phải đổi `LLM_PROVIDER` thủ công).

---

