"""Services."""
from src.services.invite_service import (
    create_invite,
    delete_invite,
    generate_invite_code,
    get_active_invites,
    get_invite_by_code,
    use_invite,
)
from src.services.media_service import (
    save_document,
    save_photo,
    save_video,
)
from src.services.notification_service import (
    notify_admin_truck_completed,
    notify_next_worker,
    notify_qc_new_work,
    notify_worker_approved,
    notify_worker_rejected,
)
from src.services.qc_service import (
    approve_step,
    get_qc_history,
    get_qc_queue,
    get_qc_stats,
    get_queue_count,
    get_step_for_review,
    reject_step,
)
from src.services.stats_service import (
    get_admin_stats,
    get_qc_full_stats,
    get_worker_full_stats,
)
from src.services.truck_service import (
    create_truck,
    delete_truck,
    get_truck_by_id,
    get_truck_by_serial,
    get_trucks_page,
)
from src.services.truck_step_service import (
    claim_step,
    get_step_by_id,
    get_step_with_truck,
    get_worker_history,
    get_worker_stats,
    get_worker_tasks,
    submit_step,
)


__all__ = [
    "approve_step",
    "claim_step",
    "create_invite",
    # Truck
    "create_truck",
    "delete_invite",
    "delete_truck",
    # Invite
    "generate_invite_code",
    "get_active_invites",
    # Stats
    "get_admin_stats",
    "get_invite_by_code",
    "get_qc_full_stats",
    "get_qc_history",
    # QC
    "get_qc_queue",
    "get_qc_stats",
    "get_queue_count",
    "get_step_by_id",
    "get_step_for_review",
    "get_step_with_truck",
    "get_truck_by_id",
    "get_truck_by_serial",
    "get_trucks_page",
    "get_worker_full_stats",
    "get_worker_history",
    "get_worker_stats",
    # TruckStep
    "get_worker_tasks",
    "notify_admin_truck_completed",
    "notify_next_worker",
    # Notification
    "notify_qc_new_work",
    "notify_worker_approved",
    "notify_worker_rejected",
    "reject_step",
    "save_document",
    # Media
    "save_photo",
    "save_video",
    "submit_step",
    "use_invite",

]
