# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Hà Anh Tuấn
- **Student ID**: [Điền MSSV]
- **Date**: 28/07/2026
- **Role**: Test Designer & Evaluator (Role 1 + Role 5 — Product Architect & Observability)
---

## I. Technical Contribution (15 Points)

- **Modules Implementated**:
  - `config/test_cases.json` — thiết kế bộ 6 test case (TC01–TC06) cho đề tài Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả, phủ đủ 3 nhóm: 🟡 Multi-step cần tool (TC01 chính sách chung, TC02 đơn còn hạn, TC03 đơn hết hạn), 🔴 Edge case (TC04 đơn không tồn tại — bẫy hallucination, TC06 regression case-sensitivity), 🟢 Đơn giản không cần tool (TC05 chit-chat).
  - `docs/trace_eval.md` — Bảng chấm điểm Agentic Fit (Scoring Matrix), so sánh phản hồi Chatbot Baseline vs ReAct Agent trên từng test case, và mục Failed Trace ghi lại nguyên văn các lần agent thất bại.

- **Code Highlights**: Phần việc của tôi không phải viết code Python mà là **thiết kế dữ liệu kiểm thử có chủ đích**. Ví dụ TC04 (`"Đơn hàng #Z9999... giao trễ 2 tháng..."`) được viết cố ý với order_id **không tồn tại** (`Z9999` không có trong `mock_db.ORDERS`) — để kiểm tra xem cả Level 1 lẫn Level 3 có báo "không tìm thấy" trung thực hay tự bịa ra ngày giao/trạng thái đơn hàng giả. Đây chính là bẫy hallucination quan trọng nhất trong bộ test.

- **Documentation**: Trong `docs/trace_eval.md`, tôi ghi lại đối chiếu trực tiếp giữa 3 level trên cùng câu hỏi (vd TC02 `"#A1001"`): Level 1 và Level 3 cùng `grounded=True` với cùng một kết luận đúng ("đủ điều kiện, còn 12 ngày"), trong khi Level 2 luôn `grounded=False` — dùng làm bằng chứng định lượng cho báo cáo nhóm.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Khi rà log của Level 2 (Chatbot Baseline) trên TC01/TC02 (câu hỏi về chính sách đổi trả và đơn `#A1001`), câu trả lời **nghe rất hợp lý và tự tin** — không giống kiểu "hallucination lộ liễu" (không bịa ngày mua hay trạng thái đơn cụ thể) — nhưng lại đưa ra những con số "thường thấy" như *"thường 3–7 ngày, hoặc lên tới 30 ngày tùy chính sách riêng"*.
- **Log Source**: Trích từ `docs/trace_eval.md` (phần so sánh phản hồi, ghi từ output thật của `handle_query_llm_chatbot`):
  ```
  L2 (TC02): "...để biết một đơn hàng có được hỗ trợ đổi trả hay không, bạn có thể
  tham khảo các điều kiện chung sau: 1. Thời hạn đổi trả: Thường trong vòng 3-7
  ngày kể từ khi nhận hàng (tùy theo quy định riêng của từng cửa hàng)..."
  ```
- **Diagnosis**: Đây **không phải hallucination kiểu bịa sự kiện cụ thể** (không tự nhận đơn A1001 đã kiểm tra xong), nhưng cũng **không phải "safe fallback" thuần túy** — nó là một dạng thứ ba đáng lưu ý: **suy đoán số liệu "điển hình ngành" trình bày như thể có căn cứ**, trong khi chính sách thật trong `mock_db.RETURN_POLICY` hoàn toàn khác (quần áo 30 ngày, điện tử chỉ 7 ngày, không có mốc "3-7 ngày" nào). Nếu chỉ phân loại nhị phân "đúng/sai" hoặc "hallucinate/không", ta sẽ bỏ lỡ loại lỗi tinh vi này — nó nguy hiểm hơn hallucination lộ liễu vì nghe rất đáng tin.
- **Solution**: Bổ sung tiêu chí phân loại thứ ba trong `docs/trace_eval.md` khi chấm output: ngoài *correct / safe fallback / hallucinated*, tôi thêm nhãn **"generic-plausible-but-ungrounded"** cho các trường hợp như trên — giúp Role Prompt Engineer nhận diện rõ Chatbot baseline không hề an toàn tuyệt đối như cái tên "safe fallback" nghe có vẻ vậy.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Cùng nhìn qua lăng kính đánh giá, sự khác biệt lớn nhất tôi thấy không phải ở "câu trả lời nghe mượt hay không" mà ở **có bằng chứng (Observation) đứng sau câu trả lời hay không**. Đây là lý do tôi luôn ưu tiên đọc field `tool_calls`/`grounded` trước khi đọc `answer` khi chấm test case.
2. **Reliability**: Agent có thể "kém tin cậy hơn" theo nghĩa vận hành — cần nhiều lượt gọi LLM hơn nên dễ dính lỗi quota/API hơn Chatbot (đã quan sát nhiều lần khi chạy `run_all_agent_tests()` bị `429 RESOURCE_EXHAUSTED` giữa chừng, khiến một số test case không thể chấm được trong lần chạy đó).
3. **Observation**: Vai trò Observability của tôi phụ thuộc hoàn toàn vào việc Observation phải trung thực — nếu tầng Tool trả sai (như bug case-sensitivity mà nhóm phát hiện ở TC06), toàn bộ báo cáo so sánh của tôi cũng sai theo. Điều này cho tôi thấy vai trò Test Designer/Observability không độc lập với chất lượng Tool — phải phối hợp chặt với Role Tool Engineer.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Tự động hoá việc chạy `run_all_agent_tests()` định kỳ (CI) trên cả 6 test case, xuất báo cáo PASS/FAIL thay vì đọc trace bằng mắt như hiện tại (Option 5 trong `src/app.py` đã có bước đầu, cần nối vào pipeline CI).
- **Safety**: Bổ sung ground truth `required_tools`/`forbidden_tools` cho từng test case trong `test_cases.json`, viết hàm so khớp tự động tool Agent thực sự gọi — để không phải đọc trace thủ công mới biết Agent có "gọi đúng tool" hay không.
- **Performance**: Thêm test case đo số bước (`steps_used`) trung bình cần thiết để đạt Final Answer, giúp phát hiện sớm nếu một thay đổi prompt làm Agent cần nhiều bước hơn bất thường.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
