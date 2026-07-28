"""
🤖 CẤP ĐỘ 1: RULE-BASED BOT (Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả)

Đây là bậc thấp nhất trong thang 4 cấp độ AI hội thoại của bài Lab. Toàn bộ
logic bên dưới KHÔNG gọi bất kỳ LLM nào — chỉ dùng regex để trích xuất
order_id và keyword matching (if/else) để phân loại intent, sau đó tra cứu
trực tiếp trong src/data/mock_db.py. Vì vậy cùng một câu hỏi luôn cho ra
đúng một kết quả (deterministic), và không bao giờ "bịa" dữ liệu không có
thật — nếu không tìm thấy, trả lời rõ ràng là không tìm thấy.

Dùng làm baseline để so sánh với:
- Level 2 (LLM Chatbot thuần, không tool) — nói mượt hơn nhưng có nguy cơ
  hallucinate vì không tra cứu dữ liệu thật.
- Level 3/4 (ReAct / Autonomous Agent) — linh hoạt hơn với câu hỏi diễn đạt
  tự do, đa bước, nhưng chi phí orchestration cao hơn.
"""

import json
import os
import re
import sys
from datetime import date

# Cho phép import mock_db hoạt động dù chạy bằng:
#   python -m src.ai_levels.level1_rule_based   (khuyến nghị, từ thư mục gốc repo)
#   python src/ai_levels/level1_rule_based.py   (chạy trực tiếp file)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_THIS_DIR)
_REPO_ROOT = os.path.dirname(_SRC_DIR)
for _p in (_REPO_ROOT, _SRC_DIR):
    if _p not in sys.path:
        sys.path.append(_p)

try:
    from src.data import mock_db
except ImportError:  # fallback khi chạy trực tiếp file (không có package "src")
    from data import mock_db

# Đảm bảo in tiếng Việt/emoji không lỗi trên Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# RULE 1 — Regex trích xuất order_id.
# Định dạng: 1-2 chữ cái + 3-6 chữ số (vd "A1001", "Z9999"), cho phép có
# dấu '#' phía trước ("#A1001"). Giới hạn 1-2 chữ cái để KHÔNG khớp nhầm
# với mã khách hàng ("CUS001") hay mã sản phẩm ("PRD001"), vốn có tiền tố
# 3 chữ cái trong mock_db.py.
# ---------------------------------------------------------------------------
ORDER_ID_PATTERN = re.compile(r"#?([A-Za-z]{1,2}\d{3,6})\b")

# RULE 2 — Keyword matching nhận diện câu hỏi về chính sách chung
# (không gắn với một đơn hàng cụ thể).
POLICY_KEYWORDS = ["chính sách", "quy định", "điều kiện"]


def extract_order_id(text: str) -> str | None:
    """Regex-match order_id dạng chữ cái+số (vd A1001); trả None nếu không có."""
    match = ORDER_ID_PATTERN.search(text)
    return match.group(1).upper() if match else None


def detect_intent(order_id: str | None, text: str) -> str:
    """
    Phân loại intent bằng keyword matching if/else thuần (không LLM).

    - Có order_id -> "check_return_eligibility" (ưu tiên cao nhất: người
      dùng đang hỏi về một đơn cụ thể, kể cả khi câu cũng chứa từ khóa
      chính sách, vd "đơn #A1001 có đúng chính sách không?").
    - Không có order_id NHƯNG có từ khóa chính sách -> "policy_question".
    - Còn lại -> "unknown".
    """
    if order_id:
        return "check_return_eligibility"
    text_lower = text.lower()
    if any(kw in text_lower for kw in POLICY_KEYWORDS):
        return "policy_question"
    return "unknown"


def _answer_policy_question() -> tuple[str, int]:
    """Liệt kê chính sách đổi trả từng category, tra thật qua mock_db (không bịa)."""
    tool_calls = 0
    lines = []
    for policy_row in mock_db.RETURN_POLICY:
        policy = mock_db.find_policy_by_category(policy_row["category"])
        tool_calls += 1
        lines.append(
            f"- {policy['category']}: đổi trả trong {policy['return_window_days']} ngày "
            f"(điều kiện: {policy['condition']})"
        )
    answer = "Chính sách đổi trả hiện áp dụng theo từng loại sản phẩm:\n" + "\n".join(lines)
    return answer, tool_calls


def _answer_check_return_eligibility(order_id: str) -> tuple[str, int, bool]:
    """Tra cứu đơn hàng thật qua mock_db rồi tính hạn đổi trả. Trả (answer, tool_calls, grounded)."""
    tool_calls = 0

    order = mock_db.find_order_by_id(order_id)
    tool_calls += 1
    if order is None:
        answer = (
            f"Không tìm thấy đơn hàng {order_id} trong hệ thống. "
            f"Vui lòng kiểm tra lại mã đơn hàng."
        )
        return answer, tool_calls, True

    if order["status"] == "shipping":
        answer = (
            f"Đơn hàng {order_id} đang trong quá trình vận chuyển (chưa giao), "
            f"nên chưa thể yêu cầu đổi trả."
        )
        return answer, tool_calls, True
    if order["status"] == "cancelled":
        answer = f"Đơn hàng {order_id} đã bị hủy, không áp dụng chính sách đổi trả."
        return answer, tool_calls, True
    if order["status"] != "delivered":
        answer = (
            f"Đơn hàng {order_id} đang ở trạng thái '{order['status']}', "
            f"hiện chưa hỗ trợ đổi trả ở trạng thái này."
        )
        return answer, tool_calls, True

    product = mock_db.find_product_by_id(order["product_id"])
    tool_calls += 1
    if product is None:
        answer = (
            f"Đơn hàng {order_id} hợp lệ nhưng không tra được thông tin sản phẩm "
            f"(product_id={order['product_id']} không tồn tại trong hệ thống)."
        )
        return answer, tool_calls, True

    policy = mock_db.find_policy_by_category(product["category"])
    tool_calls += 1
    if policy is None:
        answer = (
            f"Đơn hàng {order_id} thuộc danh mục '{product['category']}' "
            f"nhưng chưa có chính sách đổi trả cho danh mục này."
        )
        return answer, tool_calls, True

    days_passed = (date.today() - date.fromisoformat(order["order_date"])).days
    remaining = policy["return_window_days"] - days_passed

    if remaining >= 0:
        answer = (
            f"Đơn hàng {order_id} ({product['product_name']}) ĐỦ ĐIỀU KIỆN đổi trả. "
            f"Đã qua {days_passed} ngày kể từ ngày mua, còn trong hạn "
            f"{policy['return_window_days']} ngày (còn lại {remaining} ngày). "
            f"Điều kiện: {policy['condition']}."
        )
    else:
        over_days = -remaining
        answer = (
            f"Đơn hàng {order_id} ({product['product_name']}) ĐÃ HẾT HẠN đổi trả. "
            f"Đã qua {days_passed} ngày, vượt hạn {policy['return_window_days']} ngày "
            f"là {over_days} ngày."
        )

    return answer, tool_calls, True


def handle_query_rule_based(user_query: str) -> dict:
    """
    Xử lý câu hỏi bằng luật if/else + regex thuần, KHÔNG gọi LLM.

    Cách rule-matching hoạt động:
    1. Regex `ORDER_ID_PATTERN` tìm order_id dạng "1-2 chữ cái + 3-6 chữ số"
       (cho phép có dấu '#' phía trước, ví dụ "#A1001").
    2. Keyword matching trên `POLICY_KEYWORDS` để phát hiện câu hỏi về
       chính sách chung. order_id được ưu tiên hơn: nếu có order_id, luôn
       xử lý theo hướng "check_return_eligibility" cho một đơn cụ thể.
    3. Mọi câu trả lời tra cứu thật qua các hàm trong `src/data/mock_db.py`
       (find_order_by_id, find_product_by_id, find_policy_by_category) —
       không có nhánh nào tự bịa dữ liệu; nếu không tìm thấy, nói rõ là
       không tìm thấy.

    Args:
        user_query (str): Câu hỏi gốc của người dùng.

    Returns:
        dict: {
            "level": "level1_rule_based",
            "query": str,
            "intent_detected": str,
            "tool_calls": int,
            "answer": str,
            "grounded": bool,
        }
    """
    order_id = extract_order_id(user_query)
    intent = detect_intent(order_id, user_query)

    tool_calls = 0
    grounded = False

    if intent == "check_return_eligibility":
        answer, tool_calls, grounded = _answer_check_return_eligibility(order_id)
    elif intent == "policy_question":
        answer, tool_calls = _answer_policy_question()
        grounded = True
    else:  # unknown
        answer = (
            "Xin lỗi, tôi chưa hiểu rõ yêu cầu của bạn. Bạn vui lòng cung cấp "
            "mã đơn hàng (ví dụ: A1001) hoặc diễn đạt lại câu hỏi liên quan đến "
            "đổi trả / chính sách đổi trả nhé."
        )

    return {
        "level": "level1_rule_based",
        "query": user_query,
        "intent_detected": intent,
        "tool_calls": tool_calls,
        "answer": answer,
        "grounded": grounded,
    }


if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 1: RULE-BASED BOT (Order & Return Assistant) ===\n")
    test_queries = [
        "Chính sách đổi trả của cửa hàng là gì?",
        "Đơn hàng #A1001 của tôi có đổi trả được không?",
        "Tôi mua đơn #A1004 cách đây lâu rồi, giờ muốn đổi có được không?",
        "Đơn hàng #Z9999 của tôi giao trễ 2 tháng, đổi trả giúp tôi luôn nhé.",
        "Bạn khỏe không?",
    ]
    for i, q in enumerate(test_queries, start=1):
        result = handle_query_rule_based(q)
        print(f"--- Test {i} ---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
