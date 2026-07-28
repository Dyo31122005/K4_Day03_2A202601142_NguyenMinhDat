"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi cho đề tài
Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả.

Mọi tool ở đây tra cứu qua src/data/mock_db.py (KHÔNG sửa file đó), và đều
là READ-ONLY, TRỪ create_return_request có side effect (ghi thêm 1 record
vào RETURN_REQUESTS). Tool KHÔNG BAO GIỜ để exception lọt ra ngoài — mọi
lỗi (không tìm thấy đơn, tham số sai, lỗi hệ thống...) đều được bắt và trả
về dưới dạng CHUỖI mô tả lỗi rõ ràng (tiền tố "LỖI:"), để Agent đọc được
như một Observation bình thường thay vì làm crash cả vòng lặp ReAct.
"""

import os
import sys
from datetime import date

# Cho phép import mock_db hoạt động dù chạy trực tiếp file này hay import
# từ package (vd `from src import tools` trong level3_reactive_agent.py).
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
for _p in (_REPO_ROOT, _THIS_DIR):
    if _p not in sys.path:
        sys.path.append(_p)

try:
    from src.data import mock_db
except ImportError:  # fallback khi chạy trực tiếp file (không có package "src")
    from data import mock_db


def lookup_order(order_id: str) -> str:
    """
    Tra cứu thông tin một đơn hàng theo mã đơn.

    Tool contract:
        - Purpose: Dùng khi cần biết trạng thái/chi tiết một đơn hàng cụ
          thể trước khi trả lời câu hỏi liên quan đến đơn đó.
        - Input schema: order_id (str, bắt buộc) — ví dụ "A1001".
        - Output schema: chuỗi mô tả đơn hàng (ngày đặt, số lượng, tổng
          tiền, trạng thái) nếu tìm thấy; chuỗi bắt đầu bằng "LỖI:" nếu
          không tìm thấy hoặc có sự cố tra cứu.
        - Error semantics: order_id không tồn tại -> "LỖI: Không tìm thấy
          đơn hàng '...' trong hệ thống." (không raise, không bịa dữ liệu).
        - Side effect: Read-only.
        - Example: lookup_order("A1001") -> "Đơn hàng A1001: ngày đặt
          2026-07-10, số lượng 2, tổng tiền 378,000 VNĐ, trạng thái: delivered."
        - Safety: Luôn trả về string, không bao giờ raise exception.

    Args:
        order_id (str): Mã đơn hàng cần tra cứu.

    Returns:
        str: Thông tin đơn hàng, hoặc thông báo lỗi (tiền tố "LỖI:").
    """
    try:
        order = mock_db.find_order_by_id(order_id)
    except Exception as e:
        return f"LỖI: Tra cứu đơn hàng thất bại do lỗi hệ thống ({e})."

    if order is None:
        return f"LỖI: Không tìm thấy đơn hàng '{order_id}' trong hệ thống."

    return (
        f"Đơn hàng {order['order_id']}: ngày đặt {order['order_date']}, "
        f"số lượng {order['quantity']}, tổng tiền {order['total_amount']:,} VNĐ, "
        f"trạng thái: {order['status']}."
    )


def check_return_eligibility(order_id: str) -> str:
    """
    Kiểm tra một đơn hàng còn trong hạn đổi trả hay không.

    Tool contract:
        - Purpose: Dùng để kết luận một đơn hàng có đủ điều kiện đổi trả
          không (tự tra thêm sản phẩm + chính sách theo category).
        - Input schema: order_id (str, bắt buộc).
        - Output schema: chuỗi kết luận rõ ràng (đủ điều kiện / hết hạn /
          chưa giao / đã hủy / không tìm thấy), kèm số ngày cụ thể.
        - Error semantics: order_id không tồn tại, hoặc product/policy
          liên quan không tra được -> "LỖI: ..." rõ ràng, không bịa.
        - Side effect: Read-only.
        - Example: check_return_eligibility("A1004") -> "Đơn hàng A1004
          (Tai nghe bluetooth) ĐÃ HẾT HẠN đổi trả. Đã qua 87 ngày, vượt
          hạn 7 ngày là 80 ngày."
        - Safety: Luôn trả về string, không bao giờ raise exception.

    Args:
        order_id (str): Mã đơn hàng cần kiểm tra.

    Returns:
        str: Kết luận về khả năng đổi trả, hoặc thông báo lỗi (tiền tố "LỖI:").
    """
    try:
        order = mock_db.find_order_by_id(order_id)
    except Exception as e:
        return f"LỖI: Kiểm tra đổi trả thất bại do lỗi hệ thống ({e})."

    if order is None:
        return f"LỖI: Không tìm thấy đơn hàng '{order_id}' trong hệ thống."

    if order["status"] == "shipping":
        return (
            f"Đơn hàng {order_id} đang trong quá trình vận chuyển (chưa giao), "
            f"nên chưa thể yêu cầu đổi trả."
        )
    if order["status"] == "cancelled":
        return f"Đơn hàng {order_id} đã bị hủy, không áp dụng chính sách đổi trả."
    if order["status"] != "delivered":
        return (
            f"Đơn hàng {order_id} đang ở trạng thái '{order['status']}', "
            f"hiện chưa hỗ trợ đổi trả ở trạng thái này."
        )

    product = mock_db.find_product_by_id(order["product_id"])
    if product is None:
        return (
            f"LỖI: Đơn hàng {order_id} hợp lệ nhưng không tra được thông tin "
            f"sản phẩm (product_id={order['product_id']} không tồn tại)."
        )

    policy = mock_db.find_policy_by_category(product["category"])
    if policy is None:
        return (
            f"LỖI: Đơn hàng {order_id} thuộc danh mục '{product['category']}' "
            f"nhưng chưa có chính sách đổi trả cho danh mục này."
        )

    days_passed = (date.today() - date.fromisoformat(order["order_date"])).days
    remaining = policy["return_window_days"] - days_passed

    if remaining >= 0:
        return (
            f"Đơn hàng {order_id} ({product['product_name']}) ĐỦ ĐIỀU KIỆN đổi trả. "
            f"Đã qua {days_passed} ngày kể từ ngày mua, còn trong hạn "
            f"{policy['return_window_days']} ngày (còn lại {remaining} ngày). "
            f"Điều kiện: {policy['condition']}."
        )

    over_days = -remaining
    return (
        f"Đơn hàng {order_id} ({product['product_name']}) ĐÃ HẾT HẠN đổi trả. "
        f"Đã qua {days_passed} ngày, vượt hạn {policy['return_window_days']} ngày "
        f"là {over_days} ngày."
    )


def create_return_request(order_id: str, reason: str) -> str:
    """
    Tạo một yêu cầu đổi trả chính thức cho một đơn hàng (CÓ SIDE EFFECT).

    Tool contract:
        - Purpose: Dùng SAU KHI đã xác nhận đơn hàng đủ điều kiện đổi trả
          (qua check_return_eligibility), để ghi nhận yêu cầu chính thức.
        - Input schema: order_id (str, bắt buộc), reason (str, bắt buộc —
          lý do đổi trả do người dùng cung cấp).
        - Output schema: chuỗi xác nhận kèm request_id nếu thành công;
          "LỖI: ..." nếu order_id không tồn tại (không tạo record).
        - Error semantics: order_id không tồn tại -> "LỖI: Không tìm thấy
          đơn hàng, không thể tạo yêu cầu đổi trả." KHÔNG ghi record rác.
        - Side effect: Ghi thêm 1 dict mới vào mock_db.RETURN_REQUESTS
          (qua mock_db.append_return_request) — đây là tool DUY NHẤT
          trong file này làm thay đổi trạng thái hệ thống.
        - Example: create_return_request("A1001", "Sản phẩm không vừa size")
          -> "Đã tạo yêu cầu đổi trả RTN001 cho đơn hàng A1001."
        - Safety: Luôn trả về string, không bao giờ raise exception. Không
          tạo request nếu đơn hàng không tồn tại (tránh ghi rác dữ liệu giả).

    Args:
        order_id (str): Mã đơn hàng cần đổi trả.
        reason (str): Lý do đổi trả.

    Returns:
        str: Xác nhận đã tạo yêu cầu (kèm request_id), hoặc thông báo lỗi
             (tiền tố "LỖI:").
    """
    try:
        order = mock_db.find_order_by_id(order_id)
    except Exception as e:
        return f"LỖI: Tạo yêu cầu đổi trả thất bại do lỗi hệ thống ({e})."

    if order is None:
        return (
            f"LỖI: Không tìm thấy đơn hàng '{order_id}' trong hệ thống, "
            f"không thể tạo yêu cầu đổi trả."
        )

    try:
        request = mock_db.append_return_request(order_id, reason, status="pending")
    except Exception as e:
        return f"LỖI: Không thể ghi yêu cầu đổi trả ({e})."

    return (
        f"Đã tạo yêu cầu đổi trả {request['request_id']} cho đơn hàng {order_id} "
        f"(lý do: {reason}). Trạng thái: {request['status']}."
    )


# Danh sách các tool được đăng ký để Agent sử dụng — chỉ những tool trong
# dict này mới được phép gọi (xem level3_reactive_agent.py).
AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_return_eligibility": check_return_eligibility,
    "create_return_request": create_return_request,
}
