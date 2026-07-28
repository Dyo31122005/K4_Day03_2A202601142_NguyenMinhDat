"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)

Entry point CLI DUY NHẤT cho demo "Chatbot vs ReAct Agent". File này CHỈ
là lớp điều phối UI/CLI — gọi lại đúng các hàm handle_query_* đã có sẵn ở
src/ai_levels/level1_rule_based.py, level2_llm_chatbot.py,
level3_reactive_agent.py. KHÔNG chứa logic nghiệp vụ mới (không tự tra
mock_db, không tự parse ReAct...).

Chạy: python -m src.app (khuyến nghị, từ thư mục gốc repo)
"""

import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
for _p in (_REPO_ROOT, _THIS_DIR):
    if _p not in sys.path:
        sys.path.append(_p)

# Đảm bảo in/đọc tiếng Việt/emoji không lỗi trên Windows Console (cả
# stdout lẫn stdin — thiếu stdin sẽ làm input() giải mã sai khi nhận
# UTF-8 qua pipe/redirect, dù output vẫn hiển thị đúng).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

# Bật xử lý VT100/ANSI trên cmd.exe Windows 10+ để in đậm (bold) hoạt động.
# Nếu terminal không hỗ trợ, escape code chỉ dư thừa vô hại, answer vẫn
# hiển thị rõ ràng nhờ khung "=" bao quanh (không phụ thuộc vào bold).
if os.name == "nt":
    os.system("")

from dotenv import load_dotenv

load_dotenv()

try:
    from src.ai_levels.level1_rule_based import handle_query_rule_based
    from src.ai_levels.level2_llm_chatbot import handle_query_llm_chatbot
    from src.ai_levels.level3_reactive_agent import handle_query_reactive_agent
    from src.providers import get_llm_provider
except ImportError:  # fallback khi chạy trực tiếp file (không có package "src")
    from ai_levels.level1_rule_based import handle_query_rule_based
    from ai_levels.level2_llm_chatbot import handle_query_llm_chatbot
    from ai_levels.level3_reactive_agent import handle_query_reactive_agent
    from providers import get_llm_provider

BOLD = "\033[1m"
RESET = "\033[0m"

LEVEL_LABELS = {
    1: "Level 1 - Rule-Based",
    2: "Level 2 - LLM Chatbot (baseline, không tool)",
    3: "Level 3 - ReAct Agent (có tool)",
}


def load_test_cases() -> list:
    """Đọc bộ test cases từ config/test_cases.json."""
    config_path = os.path.join(_REPO_ROOT, "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_level(level: int, query: str, provider=None) -> dict:
    """
    Gọi đúng hàm handle_query_* tương ứng với level đã có sẵn ở 3 file
    level. Bọc try/except: nếu lỗi (vd quota API, lỗi provider), trả về
    một dict lỗi rõ ràng thay vì để crash cả chương trình.
    """
    try:
        if level == 1:
            return handle_query_rule_based(query)
        if level == 2:
            return handle_query_llm_chatbot(query, provider=provider)
        if level == 3:
            return handle_query_reactive_agent(query, provider=provider)
        raise ValueError(f"Level không hợp lệ: {level}")
    except Exception as e:
        return {
            "level": f"level{level}_error",
            "query": query,
            "intent_detected": None,
            "tool_calls": 0,
            "steps_used": 0,
            "max_steps_reached": False,
            "answer": f"[LỖI khi chạy Level {level}]: {e}",
            "grounded": False,
            "trace": [],
        }


def _truncate(text: str, max_len: int) -> str:
    text = (text or "").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def print_result_detail(result: dict) -> None:
    """In kết quả 1 level dạng dễ đọc; nếu có 'trace' (level3) in luôn từng step."""
    print(f"\n{'=' * 60}")
    print(f"{BOLD}✅ ANSWER:{RESET}")
    print(f"{BOLD}{result.get('answer')}{RESET}")
    print("=" * 60)
    print(f"tool_calls : {result.get('tool_calls')}")
    if "steps_used" in result:
        print(f"steps_used : {result.get('steps_used')}")
    if "max_steps_reached" in result:
        print(f"max_steps_reached: {result.get('max_steps_reached')}")
    print(f"grounded   : {result.get('grounded')}")

    trace = result.get("trace")
    if trace:
        print("\n--- TRACE (Thought -> Action -> Observation) ---")
        for t in trace:
            print(f"[Step {t['step']}] Thought: {t['thought']}")
            if t.get("action") is not None:
                print(f"           Action: {t['action']}")
            if t.get("observation") is not None:
                print(f"           Observation: {t['observation']}")


def run_option_single_level(level: int, provider) -> None:
    query = input(f"\nNhập câu hỏi cho {LEVEL_LABELS[level]}: ").strip()
    if not query:
        print("⚠️ Câu hỏi rỗng, huỷ thao tác.")
        return
    result = call_level(level, query, provider=provider)
    print_result_detail(result)


def run_option_compare(provider) -> None:
    """Option 4: chạy 1 câu hỏi qua cả 3 level, in bảng so sánh cạnh nhau."""
    query = input("\nNhập câu hỏi để so sánh cả 3 level: ").strip()
    if not query:
        print("⚠️ Câu hỏi rỗng, huỷ thao tác.")
        return

    print(f"\nCâu hỏi: {query}\n")

    rows = [(level, call_level(level, query, provider=provider)) for level in (1, 2, 3)]

    # Bảng so sánh — answer bị cắt ngắn theo độ rộng cột cố định để KHÔNG
    # vỡ format khi answer dài; bản đầy đủ được in riêng ngay bên dưới bảng.
    answer_w = 50
    header = f"| {'Level':<5} | {'Answer (rút gọn)':<{answer_w}} | {'Tool calls':<10} | {'Grounded':<8} |"
    sep = f"|{'-' * 7}|{'-' * (answer_w + 2)}|{'-' * 12}|{'-' * 10}|"
    print(header)
    print(sep)
    for level, result in rows:
        answer_short = _truncate(result.get("answer", ""), answer_w)
        print(
            f"| L{level:<4} | {answer_short:<{answer_w}} | "
            f"{str(result.get('tool_calls', 0)):<10} | {str(result.get('grounded')):<8} |"
        )

    print("\n--- CÂU TRẢ LỜI ĐẦY ĐỦ TỪNG LEVEL ---")
    for level, result in rows:
        print(f"\n[L{level}] {LEVEL_LABELS[level]}")
        print(f"{BOLD}{result.get('answer')}{RESET}")


def run_option_batch(provider) -> None:
    """Option 5: chạy toàn bộ test case trong config/test_cases.json qua 1 level, tổng kết PASS/FAIL."""
    raw_level = input("\nChọn level để chạy toàn bộ test case (1/2/3): ").strip()
    if raw_level not in ("1", "2", "3"):
        print("⚠️ Level không hợp lệ, chỉ nhận 1, 2 hoặc 3.")
        return
    level = int(raw_level)

    try:
        test_cases = load_test_cases()
    except Exception as e:
        print(f"⚠️ Không đọc được config/test_cases.json: {e}")
        return

    print(f"\n=== Chạy {len(test_cases)} test case qua {LEVEL_LABELS[level]} ===\n")

    passed = 0
    failed = 0
    for case in test_cases:
        question = case.get("question", "")
        expected = case.get("expected_behavior", "")
        result = call_level(level, question, provider=provider)
        answer = result.get("answer", "")

        # So khớp thủ công đơn giản (không dùng AI chấm điểm): coi là PASS
        # nếu có answer và answer không phải thông báo lỗi hệ thống.
        is_pass = bool(answer) and "[LỖI khi chạy Level" not in answer
        status = "✅ PASS" if is_pass else "❌ FAIL"
        passed += 1 if is_pass else 0
        failed += 0 if is_pass else 1

        print(f"[{case.get('id')}] {question}")
        print(f"  Kỳ vọng   : {expected}")
        print(f"  Answer    : {_truncate(answer, 200)}")
        print(f"  tool_calls: {result.get('tool_calls')} | grounded: {result.get('grounded')} | {status}\n")

    print("=" * 40)
    print(f"TỔNG KẾT: {passed} PASS / {failed} FAIL / {len(test_cases)} test case")
    print("=" * 40)


def print_menu() -> None:
    print("\n" + "=" * 35)
    print("DEMO: Chatbot vs ReAct Agent")
    print("=" * 35)
    print("1. Level 1 - Rule-Based")
    print("2. Level 2 - LLM Chatbot (baseline, không tool)")
    print("3. Level 3 - ReAct Agent (có tool)")
    print("4. Chạy demo nhanh: so sánh cả 3 level trên cùng 1 câu hỏi")
    print("5. Chạy toàn bộ test case (config/test_cases.json) trên 1 level")
    print("0. Thoát")


def main() -> None:
    print("=" * 50)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 50)

    try:
        provider = get_llm_provider()
        model_name = getattr(provider, "model_name", "Offline Mock Mode")
        print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    except Exception as e:
        print(f"⚠️ Không khởi tạo được LLM Provider: {e}")
        provider = None

    while True:
        print_menu()
        choice = input("Chọn: ").strip()

        if choice == "0":
            print("👋 Tạm biệt!")
            break
        elif choice == "1":
            run_option_single_level(1, provider)
        elif choice == "2":
            run_option_single_level(2, provider)
        elif choice == "3":
            run_option_single_level(3, provider)
        elif choice == "4":
            run_option_compare(provider)
        elif choice == "5":
            run_option_batch(provider)
        else:
            print("⚠️ Lựa chọn không hợp lệ, vui lòng chọn lại.")


if __name__ == "__main__":
    main()
