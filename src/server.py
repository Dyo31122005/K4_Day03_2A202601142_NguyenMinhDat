"""
🌐 WEB SERVER (Nối backend với front_end/)

Lớp điều phối HTTP mỏng — giống tinh thần của src/app.py (CLI), nhưng phục
vụ giao diện web trong front_end/code.html thay vì terminal. KHÔNG chứa
logic nghiệp vụ mới: mọi câu hỏi đều được xử lý qua call_level() (đã có
sẵn trong src/app.py), vốn tự gọi đúng handle_query_rule_based /
handle_query_llm_chatbot / handle_query_reactive_agent.

Route:
    GET  /            -> trả về front_end/code.html
    POST /api/query   -> {"level": 1|2|3, "question": "..."} -> JSON kết quả

Chạy: python -m src.server (khuyến nghị, từ thư mục gốc repo), sau đó mở
http://127.0.0.1:5000/ trên trình duyệt.
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
_FRONTEND_DIR = os.path.join(_REPO_ROOT, "front_end")
for _p in (_REPO_ROOT, _THIS_DIR):
    if _p not in sys.path:
        sys.path.append(_p)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request, send_from_directory

try:
    from src.app import call_level, LEVEL_LABELS
    from src.providers import get_llm_provider
except ImportError:  # fallback khi chạy trực tiếp file (không có package "src")
    from app import call_level, LEVEL_LABELS
    from providers import get_llm_provider

app = Flask(__name__, static_folder=None)

# Khởi tạo 1 provider dùng chung cho mọi request (tránh tạo lại mỗi lần gọi).
_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_llm_provider()
    return _provider


@app.route("/")
def index():
    """Trả về giao diện chat tĩnh trong front_end/code.html."""
    return send_from_directory(_FRONTEND_DIR, "code.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    """
    Nhận {"level": 1|2|3, "question": "..."}, gọi call_level() (đã có sẵn
    trong src/app.py) và trả về JSON kết quả — cùng format với CLI.
    """
    data = request.get_json(silent=True) or {}

    level = data.get("level")
    question = str(data.get("question", "")).strip()

    if level not in (1, 2, 3):
        return jsonify({"error": "Trường 'level' phải là 1, 2 hoặc 3."}), 400
    if not question:
        return jsonify({"error": "Trường 'question' không được rỗng."}), 400

    result = call_level(level, question, provider=_get_provider())
    return jsonify(result)


@app.route("/api/health")
def health():
    """Kiểm tra nhanh server + provider đã sẵn sàng chưa (dùng khi debug)."""
    try:
        provider = _get_provider()
        model_name = getattr(provider, "model_name", "Offline Mock Mode")
        return jsonify(
            {
                "status": "ok",
                "provider": provider.__class__.__name__,
                "model": model_name,
                "levels": LEVEL_LABELS,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    print(f"🔌 Đang khởi tạo LLM Provider...")
    try:
        provider = _get_provider()
        model_name = getattr(provider, "model_name", "Offline Mock Mode")
        print(f"✅ Provider: {provider.__class__.__name__} (Model: {model_name})")
    except Exception as e:
        print(f"⚠️ Không khởi tạo được LLM Provider ngay: {e}")
        print("   (Sẽ thử lại khi có request đầu tiên.)")

    print("🌐 Server chạy tại: http://127.0.0.1:5000/")
    app.run(host="127.0.0.1", port=5000, debug=False)
