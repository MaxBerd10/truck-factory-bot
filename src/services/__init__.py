"""Services."""
from src.services.qc_service import (
    approve_step,
    get_qc_history,
    get_qc_queue,
    get_qc_stats,
    get_queue_count,
    get_step_for_review,
    reject_step,
)



from src.services.media_service import (
    save_document,
    save_photo,
    save_video,
)



from src.services.invite_service import (
    create_invite,
    delete_invite,
    generate_invite_code,
    get_active_invites,
    get_invite_by_code,
    use_invite,
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
    # Invite
    "generate_invite_code",
    "create_invite",
    "get_invite_by_code",
    "get_active_invites",
    "use_invite",
    "delete_invite",
    # Truck
    "create_truck",
    "get_truck_by_serial",
    "get_truck_by_id",
    "get_trucks_page",
    "delete_truck",
    # TruckStep
    "get_worker_tasks",
    "get_step_by_id",
    "get_step_with_truck",
    "claim_step",
    "submit_step",
    "get_worker_history",
    "get_worker_stats",

    # Media
    "save_photo",
    "save_video",
    "save_document",


    # QC
    "get_qc_queue",
    "get_step_for_review",
    "approve_step",
    "reject_step",
    "get_qc_history",
    "get_qc_stats",
    "get_queue_count",
]
