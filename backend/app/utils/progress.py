from dataclasses import dataclass
from typing import Optional, Dict
import uuid
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@dataclass
class ProgressTracker:
    """Track progress of long-running operations"""

    total: int
    current: int = 0
    status: str = ""
    start_time: float = time.time()

    def update(self, increment: int = 1, status: Optional[str] = None) -> Dict:
        self.current += increment
        if status:
            self.status = status

        elapsed = time.time() - self.start_time
        percent = (self.current / self.total) * 100

        return {
            "progress": percent,
            "current": self.current,
            "total": self.total,
            "status": self.status,
            "elapsed_seconds": elapsed,
        }


# Store progress information
_progress_trackers: Dict[str, ProgressTracker] = {}


def create_progress_tracker(total: int) -> str:
    """Create a new progress tracker and return its ID"""
    tracker_id = str(uuid.uuid4())
    _progress_trackers[tracker_id] = ProgressTracker(total=total)
    return tracker_id


def get_tracker(tracker_id: str) -> Optional[ProgressTracker]:
    """Get progress tracker by ID"""
    return _progress_trackers.get(tracker_id)


@router.get("/progress/{tracker_id}")
async def get_progress(tracker_id: str):
    """API endpoint to get current progress"""
    tracker = get_tracker(tracker_id)
    if not tracker:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Progress tracker not found"},
        )

    return JSONResponse(
        status_code=200, content={"success": True, "data": tracker.update(increment=0)}
    )
