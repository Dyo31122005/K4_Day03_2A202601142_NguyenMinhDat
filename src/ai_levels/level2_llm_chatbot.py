"""
🤖 CẤP ĐỘ 2: LLM CHATBOT (Baseline thuần — không Tool, không Grounding)

Baseline để LỘ RÕ giới hạn của một Chatbot chỉ dùng LLM: system prompt +
user message -> đúng 1 LLM call -> trả lời trực tiếp, không có bước tra
cứu dữ liệu nào. File này TUYỆT ĐỐI KHÔNG import tools.py hay mock_db.py
(kể cả để tham khảo) — đây là ranh giới cố tình của bài Lab, nhằm chứng
minh rằng khi câu hỏi cần dữ liệu đơn hàng thật (order_id, ngày mua, trạng
thái giao hàng...), một Chatbot thuần không có cách nào biết sự thật, nên
nó buộc phải:
  - Từ chối / nói không biết (safe fallback), hoặc
  - Bịa ra một câu trả lời nghe hợp lý (hallucination).

Dùng để so sánh với Level 1 (rule-based, luôn grounded qua mock_db) và
Level 3/4 (Agent có tool, có thể grounded thật sự qua ReAct loop).
"""

import json
import os
import sys

# Cho phép import prompts.py / providers.py hoạt động dù chạy bằng:
#   python -m src.ai_levels.level2_llm_chatbot   (khuyến nghị, từ thư mục gốc repo)
#   python src/ai_levels/level2_llm_chatbot.py    (chạy trực tiếp file)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_THIS_DIR)
_REPO_ROOT = os.path.dirname(_SRC_DIR)
for _p in (_REPO_ROOT, _SRC_DIR):
    if _p not in sys.path:
        sys.path.append(_p)

try:
    from src.prompts import CHATBOT_BASELINE_PROMPT
    from src.providers import get_llm_provider
except ImportError:  # fallback khi chạy trực tiếp file (không có package "src")
    from prompts import CHATBOT_BASELINE_PROMPT
    from providers import get_llm_provider

# Đảm bảo in tiếng Việt/emoji không lỗi trên Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def handle_query_llm_chatbot(user_query: str, provider=None) -> dict:
    """
    Baseline Chatbot thuần: system prompt + user message -> đúng 1 LLM call.

    KHÔNG gọi tools.py / mock_db.py trong hàm này. Khi câu hỏi cần dữ liệu
    đơn hàng thật, LLM chỉ có hai khả năng: từ chối/nói không biết, hoặc
    bịa ra một câu trả lời nghe hợp lý (hallucination) — vì nó không có
    cách nào tra cứu order_id thật. Đây chính là bằng chứng cho thấy
    Chatbot thuần thiếu grounding, cần dùng làm căn cứ so sánh với Agent.

    Args:
        user_query (str): Câu hỏi gốc của người dùng.
        provider: (tuỳ chọn) instance BaseLLMProvider đã khởi tạo sẵn từ
            providers.get_llm_provider(). Nếu không truyền, hàm tự lấy
            provider mặc định (đọc biến môi trường LLM_PROVIDER) —
            KHÔNG tự ý tạo client LLM mới trong file này.

    Returns:
        dict: {
            "level": "level2_llm_chatbot",
            "query": str,
            "intent_detected": None,   # level này không phân loại intent
            "tool_calls": 0,           # LUÔN LUÔN = 0 — điều kiện tự kiểm bắt buộc
            "answer": str,             # raw text từ LLM, không hậu xử lý
            "grounded": False,         # mặc định False, review thủ công sau
        }
    """
    if provider is None:
        provider = get_llm_provider()

    try:
        # Đúng 1 lần gọi LLM duy nhất — không retry, không gọi lần 2 dù rỗng.
        answer = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
        if not answer:
            answer = "[Chatbot Baseline]: LLM trả về phản hồi rỗng."
    except Exception as e:  # bắt lỗi timeout/lỗi provider, không được crash
        answer = f"[Chatbot Baseline Error]: Không gọi được LLM Provider ({e})."

    return {
        "level": "level2_llm_chatbot",
        "query": user_query,
        "intent_detected": None,
        "tool_calls": 0,
        "answer": answer,
        "grounded": False,
    }


def run_all_baseline_tests(test_cases_path: str = "config/test_cases.json") -> list[dict]:
    """
    Đọc config/test_cases.json, chạy handle_query_llm_chatbot cho từng câu,
    in kết quả ra console theo format:
        [ID] query
        -> answer
        (tool_calls: 0)

    Trả về list[dict] để ghi tiếp vào docs/trace_eval.md (Role Observability).
    """
    resolved_path = test_cases_path
    if not os.path.isabs(resolved_path) and not os.path.exists(resolved_path):
        resolved_path = os.path.join(_REPO_ROOT, test_cases_path)

    with open(resolved_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    # Dùng đúng 1 provider instance cho cả 5 câu, thay vì tạo mới mỗi lần gọi.
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})\n")

    results = []
    for case in test_cases:
        result = handle_query_llm_chatbot(case["question"], provider=provider)
        results.append(result)
        print(f"[{case['id']}] {case['question']}")
        print(f"-> {result['answer']}")
        print(f"(tool_calls: {result['tool_calls']})\n")

    return results


if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 2: LLM CHATBOT BASELINE (KHÔNG TOOL, KHÔNG GROUNDING) ===\n")
    run_all_baseline_tests()
