"""
mock_db.py
Mock database cho bài toán Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả.
Dữ liệu giả lập, KHÔNG chứa thông tin thật, dùng cho mục đích demo/lab.

Cấu trúc:
- CUSTOMERS: thông tin khách hàng
- PRODUCTS: danh mục sản phẩm
- ORDERS: đơn hàng
- RETURN_POLICY: chính sách đổi trả theo category
- RETURN_REQUESTS: yêu cầu đổi trả (được Agent ghi thêm khi xử lý, rỗng lúc khởi tạo)

Lưu ý: Đây là in-memory mock, dữ liệu KHÔNG persist giữa các lần chạy app.
"""

from datetime import date


# ----------------------------------------------------------------------
# BẢNG: customers
# ----------------------------------------------------------------------
CUSTOMERS = [
    {"customer_id": "CUS001", "full_name": "Nguyễn Văn An",   "phone": "0901234567", "email": "an.nguyen@gmail.com",   "registered_date": "2024-03-12"},
    {"customer_id": "CUS002", "full_name": "Trần Thị Bích",   "phone": "0912345678", "email": "bich.tran@gmail.com",   "registered_date": "2024-05-20"},
    {"customer_id": "CUS003", "full_name": "Lê Hoàng Cường",  "phone": "0923456789", "email": "cuong.le@gmail.com",    "registered_date": "2024-07-01"},
    {"customer_id": "CUS004", "full_name": "Phạm Thu Dung",   "phone": "0934567890", "email": "dung.pham@gmail.com",   "registered_date": "2024-09-15"},
    {"customer_id": "CUS005", "full_name": "Hoàng Minh Đức",  "phone": "0945678901", "email": "duc.hoang@gmail.com",   "registered_date": "2025-01-10"},
]


# ----------------------------------------------------------------------
# BẢNG: products
# ----------------------------------------------------------------------
PRODUCTS = [
    {"product_id": "PRD001", "product_name": "Áo thun cotton unisex",   "category": "quần áo",  "price": 189000},
    {"product_id": "PRD002", "product_name": "Giày sneaker trắng",      "category": "giày dép", "price": 650000},
    {"product_id": "PRD003", "product_name": "Balo laptop 15 inch",     "category": "phụ kiện", "price": 420000},
    {"product_id": "PRD004", "product_name": "Tai nghe bluetooth",      "category": "điện tử",  "price": 590000},
    {"product_id": "PRD005", "product_name": "Quần jean nam",           "category": "quần áo",  "price": 350000},
    {"product_id": "PRD006", "product_name": "Sạc dự phòng 10000mAh",   "category": "điện tử",  "price": 299000},
    {"product_id": "PRD007", "product_name": "Dép sandal nữ",           "category": "giày dép", "price": 220000},
]


# ----------------------------------------------------------------------
# BẢNG: orders
# ----------------------------------------------------------------------
ORDERS = [
    {"order_id": "A1001", "customer_id": "CUS001", "product_id": "PRD001", "order_date": "2026-07-10", "quantity": 2, "total_amount": 378000, "status": "delivered"},
    {"order_id": "A1002", "customer_id": "CUS002", "product_id": "PRD002", "order_date": "2026-06-18", "quantity": 1, "total_amount": 650000, "status": "delivered"},
    {"order_id": "A1003", "customer_id": "CUS003", "product_id": "PRD003", "order_date": "2026-07-20", "quantity": 1, "total_amount": 420000, "status": "delivered"},
    {"order_id": "A1004", "customer_id": "CUS001", "product_id": "PRD004", "order_date": "2026-05-02", "quantity": 1, "total_amount": 590000, "status": "delivered"},
    {"order_id": "A1005", "customer_id": "CUS004", "product_id": "PRD005", "order_date": "2026-07-22", "quantity": 1, "total_amount": 350000, "status": "delivered"},
    {"order_id": "A1006", "customer_id": "CUS005", "product_id": "PRD006", "order_date": "2026-07-25", "quantity": 2, "total_amount": 598000, "status": "shipping"},
    {"order_id": "A1007", "customer_id": "CUS002", "product_id": "PRD007", "order_date": "2026-04-15", "quantity": 1, "total_amount": 220000, "status": "delivered"},
    {"order_id": "A1008", "customer_id": "CUS003", "product_id": "PRD001", "order_date": "2026-07-05", "quantity": 3, "total_amount": 567000, "status": "cancelled"},
    {"order_id": "A1009", "customer_id": "CUS004", "product_id": "PRD002", "order_date": "2026-07-26", "quantity": 1, "total_amount": 650000, "status": "delivered"},
    {"order_id": "A1010", "customer_id": "CUS005", "product_id": "PRD003", "order_date": "2026-06-01", "quantity": 1, "total_amount": 420000, "status": "delivered"},
    {"order_id": "A1011", "customer_id": "CUS001", "product_id": "PRD006", "order_date": "2026-07-15", "quantity": 1, "total_amount": 299000, "status": "delivered"},
    {"order_id": "A1012", "customer_id": "CUS002", "product_id": "PRD004", "order_date": "2026-03-10", "quantity": 1, "total_amount": 590000, "status": "delivered"},
]
# Lưu ý: order_id "Z9999" CỐ TÌNH không tồn tại trong bảng này,
# dùng làm test case bẫy để kiểm tra hallucination.


# ----------------------------------------------------------------------
# BẢNG: return_policy (đơn giản hóa cho demo)
# ----------------------------------------------------------------------
RETURN_POLICY = [
    {"category": "quần áo",  "return_window_days": 30, "condition": "còn tem, chưa qua sử dụng"},
    {"category": "giày dép", "return_window_days": 30, "condition": "còn hộp, chưa đi ngoài trời"},
    {"category": "phụ kiện", "return_window_days": 15, "condition": "còn nguyên bao bì"},
    {"category": "điện tử",  "return_window_days": 7,  "condition": "chưa kích hoạt bảo hành, còn seal"},
]


# ----------------------------------------------------------------------
# BẢNG: return_requests
# Rỗng lúc khởi tạo. Agent sẽ append record mới vào đây khi xử lý
# yêu cầu đổi trả thành công (bằng chứng "action đã thực hiện thật").
# ----------------------------------------------------------------------
RETURN_REQUESTS: list[dict] = []


# ----------------------------------------------------------------------
# HÀM TRUY VẤN CƠ BẢN (dùng nội bộ bởi tools.py)
# Đặt ở đây để tools.py chỉ cần gọi hàm, không cần biết cấu trúc data thô.
# ----------------------------------------------------------------------

def find_order_by_id(order_id: str) -> dict | None:
    """Trả về order dict nếu tìm thấy, None nếu không tồn tại.

    Chuẩn hóa order_id (strip + upper) trước khi so khớp, để tránh false
    negative khi order_id được truyền vào ở dạng chữ thường (vd "a1001"),
    trong khi ORDERS lưu order_id dạng chữ hoa (vd "A1001").
    """
    normalized_id = order_id.strip().upper()
    for order in ORDERS:
        if order["order_id"] == normalized_id:
            return order
    return None


def find_product_by_id(product_id: str) -> dict | None:
    """Trả về product dict nếu tìm thấy, None nếu không tồn tại."""
    for product in PRODUCTS:
        if product["product_id"] == product_id:
            return product
    return None


def find_customer_by_id(customer_id: str) -> dict | None:
    """Trả về customer dict nếu tìm thấy, None nếu không tồn tại."""
    for customer in CUSTOMERS:
        if customer["customer_id"] == customer_id:
            return customer
    return None


def find_policy_by_category(category: str) -> dict | None:
    """Trả về policy dict theo category, None nếu category không có trong bảng."""
    for policy in RETURN_POLICY:
        if policy["category"] == category:
            return policy
    return None


def append_return_request(order_id: str, reason: str, status: str) -> dict:
    """
    Tạo một return_request mới và append vào RETURN_REQUESTS.
    request_id tự sinh theo thứ tự (RTN001, RTN002, ...).
    """
    new_id = f"RTN{len(RETURN_REQUESTS) + 1:03d}"
    new_request = {
        "request_id": new_id,
        "order_id": order_id,
        "reason": reason,
        "request_date": date.today().isoformat(),
        "status": status,
    }
    RETURN_REQUESTS.append(new_request)
    return new_request