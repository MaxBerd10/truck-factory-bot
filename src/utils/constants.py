"""Loyiha konstantalari."""
from enum import Enum


# ==== Steplar ====
class StepNumber(int, Enum):
    """Truck ishlab chiqarish bosqichlari (6 ta)."""
    KARKAS = 1
    KUZOV = 2
    ICHKI_QOPLAMA = 3
    BO_YASH = 4
    ESHIK_DERAZA = 5
    YIGISH = 6


STEP_NAMES: dict[int, str] = {
    1: "1️⃣ Karkas",
    2: "2️⃣ Kuzov o'rnatish",
    3: "3️⃣ Ichki qoplama",
    4: "4️⃣ Bo'yash",
    5: "5️⃣ Eshik-deraza",
    6: "6️⃣ Yig'ish",
}

STEP_SHORT_NAMES: dict[int, str] = {
    1: "Karkas",
    2: "Kuzov",
    3: "Ichki qoplama",
    4: "Bo'yash",
    5: "Eshik-deraza",
    6: "Yig'ish",
}

TOTAL_STEPS = 6


# ==== Rollar ====
class UserRole(str, Enum):
    WORKER = "worker"
    QC = "qc"
    ADMIN = "admin"


ROLE_NAMES: dict[str, str] = {
    "worker": "👷 Ishchi",
    "qc": "🔍 Sifat nazoratchisi",
    "admin": "👑 Administrator",
}


# ==== Holatlar ====
class StepStatus(str, Enum):
    """Har bir step uchun holat."""
    PENDING = "pending"         # Boshlanmagan
    IN_REVIEW = "in_review"     # QC kutayapti
    APPROVED = "approved"       # Tasdiqlangan
    REJECTED = "rejected"       # Rad etilgan


STATUS_NAMES: dict[str, str] = {
    "pending": "⏳ Kutilmoqda",
    "in_review": "🔍 Tekshirilmoqda",
    "approved": "✅ Tasdiqlangan",
    "rejected": "❌ Rad etilgan",
}


class TruckStatus(str, Enum):
    """Truck ning umumiy holati."""
    IN_PROGRESS = "in_progress"   # Jarayonda
    COMPLETED = "completed"       # Tayyor (6-step tasdiqlangach)


TRUCK_STATUS_NAMES: dict[str, str] = {
    "in_progress": "🔧 Jarayonda",
    "completed": "✅ Tayyor",
}


# ==== Media ====
class MediaType(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


# ==== Callback data prefixlari ====
class CallbackPrefix(str, Enum):
    """Callback data uchun prefixlar (to'qnashuvni oldini oladi)."""
    # Worker
    WORKER_TASKS = "wt"
    WORKER_SUBMIT = "ws"
    WORKER_HISTORY = "wh"

    # QC
    QC_QUEUE = "qq"
    QC_APPROVE = "qa"
    QC_REJECT = "qr"

    # Admin
    ADMIN_USERS = "au"
    ADMIN_INVITES = "ai"
    ADMIN_TRUCKS = "at"
    ADMIN_STATS = "as"


# ==== Truck prioriteti ====
class TruckPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


PRIORITY_NAMES: dict[str, str] = {
    "low": "🟢 Past",
    "normal": "🔵 Oddiy",
    "high": "🟠 Yuqori",
    "urgent": "🔴 Shoshilinch",
}


# ==== Truck manbasi ====
class TruckSource(str, Enum):
    ADMIN = "admin"    # Admin qo'lda qo'shdi
    ERP = "erp"        # ERP dan keldi


SOURCE_NAMES: dict[str, str] = {
    "admin": "👤 Admin",
    "erp": "🌐 ERP",
}
