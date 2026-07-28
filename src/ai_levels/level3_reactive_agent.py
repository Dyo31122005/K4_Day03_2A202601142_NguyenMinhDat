"""
🧠 CẤP ĐỘ 3: REACTIVE AGENT (ReAct Agent thật — Thought -> Action -> Observation)

Đây là ReAct Agent THẬT: LLM sinh Thought + Action, code (application) tự
gọi tool tương ứng trong src/tools.py, rồi CODE (không phải LLM) tạo ra
Observation từ kết quả tool thật, chèn ngược lại vào prompt để LLM đọc ở
bước suy luận tiếp theo. Lặp lại đến khi LLM trả Final Answer hoặc chạm
`prompts.MAX_ITERATIONS` (phanh an toàn Guardrail).

Vì src/providers.py chỉ cung cấp `provider.generate(prompt, system_prompt)`
dạng single-turn (không có state hội thoại tích hợp sẵn, không có
function-calling có cấu trúc), vòng lặp này dùng ReAct kiểu TEXT-BASED:
- Toàn bộ lịch sử Thought/Action/Observation được tích luỹ vào một chuỗi
  "scratchpad" và gửi lại nguyên vẹn trong `prompt` ở mỗi lượt gọi LLM,
  vì provider không tự nhớ được các lượt gọi trước.
- Sau mỗi lần gọi LLM, code CẮT bỏ (truncate) mọi thứ xuất hiện sau nhãn
  "Observation:" trong phản hồi thô — đề phòng LLM tự bịa luôn Observation
  giả trong cùng 1 lần sinh text (vì provider không hỗ trợ stop_sequence).
  Điều này đảm bảo đúng yêu cầu bắt buộc: Observation luôn do code tạo ra
  từ kết quả tool thật, không bao giờ do LLM tự viết.

So sánh với Level 1 (rule-based, luôn grounded) và Level 2 (LLM thuần,
không tool, dễ hallucinate): Level 3 có thể grounded THẬT nhờ tool, nhưng
trả giá bằng nhiều lượt gọi LLM hơn (chi phí orchestration cao hơn).
"""

import json
import os
import re
import sys

# Cho phép import tools.py / prompts.py / providers.py hoạt động dù chạy bằng:
#   python -m src.ai_levels.level3_reactive_agent   (khuyến nghị, từ thư mục gốc repo)
#   python src/ai_levels/level3_reactive_agent.py    (chạy trực tiếp file)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_THIS_DIR)
_REPO_ROOT = os.path.dirname(_SRC_DIR)
for _p in (_REPO_ROOT, _SRC_DIR):
    if _p not in sys.path:
        sys.path.append(_p)

try:
    from src.tools import AVAILABLE_TOOLS
    from src.prompts import REACT_SYSTEM_PROMPT, MAX_ITERATIONS
    from src.providers import get_llm_provider
except ImportError:  # fallback khi chạy trực tiếp file (không có package "src")
    from tools import AVAILABLE_TOOLS
    from prompts import REACT_SYSTEM_PROMPT, MAX_ITERATIONS
    from providers import get_llm_provider

# Đảm bảo in tiếng Việt/emoji không lỗi trên Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SAFE_FALLBACK_MESSAGE = (
    "Xin lỗi, tôi cần thêm thông tin hoặc không thể hoàn tất yêu cầu này "
    "trong giới hạn xử lý, vui lòng liên hệ hỗ trợ trực tiếp."
)

# ---------------------------------------------------------------------------
# Regex parser cho định dạng text-based ReAct do REACT_SYSTEM_PROMPT quy định.
# ---------------------------------------------------------------------------
_THOUGHT_PATTERN = re.compile(
    r"Thought\s*:\s*(.*?)(?=\n\s*(?:Action|Final Answer)\s*:|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_ACTION_PATTERN = re.compile(
    r"Action\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\[(.*?)\]",
    re.DOTALL | re.IGNORECASE,
)
_FINAL_ANSWER_PATTERN = re.compile(
    r"Final Answer\s*:\s*(.*)",
    re.DOTALL | re.IGNORECASE,
)


def _split_action_args(args_str: str) -> list:
    """
    Tách các tham số trong `Action: tool[arg1, arg2]`, hỗ trợ chuỗi có dấu
    ngoặc kép chứa dấu phẩy bên trong (vd reason đổi trả). Bỏ dấu ngoặc
    kép/đơn bao quanh nếu có.
    """
    args_str = args_str.strip()
    if not args_str:
        return []
    # Tách theo dấu phẩy KHÔNG nằm trong cặp dấu ngoặc kép.
    parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', args_str)
    cleaned = []
    for part in parts:
        part = part.strip()
        if len(part) >= 2 and part[0] == part[-1] and part[0] in ("'", '"'):
            part = part[1:-1]
        cleaned.append(part)
    return cleaned


def parse_react_response(raw_text: str) -> dict:
    """
    Parse phản hồi thô của LLM thành {"type": "final"|"action"|"parser_error", ...}.

    QUAN TRỌNG: Trước khi parse, hàm CẮT bỏ mọi nội dung xuất hiện sau nhãn
    "Observation:" (nếu LLM tự ý sinh luôn cả phần đó) — Observation không
    bao giờ được lấy từ văn bản do LLM tự viết, chỉ được tạo bởi code sau
    khi gọi tool thật.
    """
    text = raw_text or ""
    obs_match = re.search(r"Observation\s*:", text, re.IGNORECASE)
    if obs_match:
        text = text[: obs_match.start()]

    thought_match = _THOUGHT_PATTERN.search(text)
    if thought_match:
        thought = thought_match.group(1).strip()
    else:
        # Không tìm thấy nhãn "Thought:" — thường do provider lỗi (timeout,
        # 503, safety block...) trả về text không đúng định dạng ReAct.
        # Giữ lại một phần raw text để còn dấu vết debug, thay vì để trống.
        thought = text.strip()[:300]

    final_match = _FINAL_ANSWER_PATTERN.search(text)
    if final_match:
        return {
            "type": "final",
            "thought": thought,
            "final_answer": final_match.group(1).strip(),
        }

    action_match = _ACTION_PATTERN.search(text)
    if action_match:
        return {
            "type": "action",
            "thought": thought,
            "tool_name": action_match.group(1).strip(),
            "args": _split_action_args(action_match.group(2)),
        }

    return {"type": "parser_error", "thought": thought}


def _is_error_observation(observation: str) -> bool:
    """Nhận diện Observation là lỗi hệ thống/tool (KHÔNG tính là grounded)."""
    return isinstance(observation, str) and observation.startswith(("LỖI: Tool", "Tool error:"))


def handle_query_reactive_agent(user_query: str, provider=None) -> dict:
    """
    Vòng lặp ReAct: Thought -> Action -> Observation -> lặp lại, cho đến
    khi có Final Answer hoặc chạm `MAX_ITERATIONS` (đọc từ prompts.py,
    không hard-code lại số).

    An toàn:
    - Chỉ được gọi các tool đã đăng ký trong `tools.AVAILABLE_TOOLS`; tool
      không tồn tại -> Observation báo lỗi rõ ràng, không crash.
    - Tool raise exception -> bắt bằng try/except, Observation = "Tool
      error: ...", không crash cả vòng lặp.
    - Action sai định dạng (không parse được tên tool/tham số) ->
      Observation = "Parser error: ..." và agent vẫn được tiếp tục vòng
      lặp (trừ khi đã chạm max_steps).
    - Chạm MAX_ITERATIONS mà chưa có Final Answer -> trả về SAFE_FALLBACK_MESSAGE,
      không lặp vô hạn, không bịa câu trả lời.

    Args:
        user_query (str): Câu hỏi gốc của người dùng.
        provider: (tuỳ chọn) instance BaseLLMProvider đã khởi tạo sẵn. Nếu
            không truyền, hàm tự lấy qua providers.get_llm_provider().

    Returns:
        dict: {
            "level": "level3_reactive_agent",
            "query": str,
            "intent_detected": None,
            "tool_calls": int,          # số lần THỰC SỰ gọi tool (không đếm Thought)
            "steps_used": int,          # tổng số vòng lặp (lượt gọi LLM) đã chạy
            "max_steps_reached": bool,
            "answer": str,
            "grounded": bool,           # True nếu có >=1 tool call thành công (kể cả "không tìm thấy")
            "trace": list[dict],        # [{"step", "thought", "action", "observation"}, ...]
        }
    """
    if provider is None:
        provider = get_llm_provider()

    trace = []
    tool_calls = 0
    grounded = False
    final_answer = None
    scratchpad = ""

    step = 0
    while step < MAX_ITERATIONS:
        step += 1
        prompt = user_query if not scratchpad else f"{user_query}\n\n{scratchpad}"

        try:
            raw_response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        except Exception as e:
            # Lỗi gọi LLM (vd timeout) -> xử lý như parser error để agent
            # còn cơ hội thử lại ở bước sau, thay vì crash toàn bộ chương trình.
            parsed = {"type": "parser_error", "thought": f"[Lỗi gọi LLM Provider: {e}]"}
        else:
            parsed = parse_react_response(raw_response)

        thought = parsed.get("thought", "")

        # --- Case: Final Answer -> dừng loop ---
        if parsed["type"] == "final":
            final_answer = parsed["final_answer"]
            trace.append({"step": step, "thought": thought, "action": None, "observation": None})
            break

        # --- Case: Parser error -> Observation báo lỗi format, agent tiếp tục lặp ---
        if parsed["type"] == "parser_error":
            observation = "Parser error: không thể hiểu định dạng action, vui lòng thử lại"
            scratchpad += f"Thought: {thought}\nAction: (không xác định)\nObservation: {observation}\n\n"
            trace.append({"step": step, "thought": thought, "action": None, "observation": observation})
            continue

        # --- Case: Action -> map sang tool thật, gọi tool, tạo Observation ---
        tool_name = parsed["tool_name"]
        args = parsed["args"]
        action_str = f"{tool_name}[{', '.join(args)}]"

        if tool_name not in AVAILABLE_TOOLS:
            observation = (
                f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ: "
                f"{', '.join(AVAILABLE_TOOLS.keys())}."
            )
        else:
            try:
                observation = AVAILABLE_TOOLS[tool_name](*args)
                tool_calls += 1
                if not _is_error_observation(observation):
                    # Tool thực thi thành công (kể cả kết quả "không tìm thấy
                    # đơn hàng" — đó vẫn là sự thật lấy từ mock_db, không phải
                    # bịa đặt) -> answer sau đó được coi là grounded.
                    grounded = True
            except Exception as e:
                observation = f"Tool error: {e}"
                tool_calls += 1  # đã thực sự gọi tool, dù tool lỗi giữa chừng

        scratchpad += f"Thought: {thought}\nAction: {action_str}\nObservation: {observation}\n\n"
        trace.append({"step": step, "thought": thought, "action": action_str, "observation": observation})

    max_steps_reached = final_answer is None
    if max_steps_reached:
        final_answer = SAFE_FALLBACK_MESSAGE

    return {
        "level": "level3_reactive_agent",
        "query": user_query,
        "intent_detected": None,
        "tool_calls": tool_calls,
        "steps_used": step,
        "max_steps_reached": max_steps_reached,
        "answer": final_answer,
        "grounded": grounded,
        "trace": trace,
    }


def run_all_agent_tests(test_cases_path: str = "config/test_cases.json") -> list:
    """
    Chạy handle_query_reactive_agent cho toàn bộ test case trong
    config/test_cases.json, in chi tiết từng step trong trace (Thought ->
    Action -> Observation) để kiểm tra bằng mắt, và trả về list[dict] để
    ghi tiếp vào docs/trace_eval.md.
    """
    resolved_path = test_cases_path
    if not os.path.isabs(resolved_path) and not os.path.exists(resolved_path):
        resolved_path = os.path.join(_REPO_ROOT, test_cases_path)

    with open(resolved_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})\n")

    results = []
    for case in test_cases:
        print("=" * 70)
        print(f"[TC{case['id']:02d}] {case['question']}")
        print("=" * 70)

        result = handle_query_reactive_agent(case["question"], provider=provider)

        for t in result["trace"]:
            print(f"--- Step {t['step']} ---")
            print(f"Thought: {t['thought']}")
            if t["action"] is not None:
                print(f"Action: {t['action']}")
            if t["observation"] is not None:
                print(f"Observation: {t['observation']}")

        print(f"\n>>> Final Answer: {result['answer']}")
        print(
            f">>> tool_calls={result['tool_calls']} | steps_used={result['steps_used']} | "
            f"max_steps_reached={result['max_steps_reached']} | grounded={result['grounded']}\n"
        )
        results.append(result)

    return results


if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 3: REACT AGENT (Thought -> Action -> Observation) ===\n")
    run_all_agent_tests()
