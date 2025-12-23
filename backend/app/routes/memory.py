from fastapi import APIRouter
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel

from app.database.images import db_get_all_images

router = APIRouter(prefix="/memories", tags=["Memories"])


class Memory(BaseModel):
    id: str
    type: str  # SPOTLIGHT | REVISIT | WEEKEND | YEAR
    title: str
    subtitle: str
    image_ids: List[str]


def parse_date(img):
    md = img.get("metadata") or {}
    date_str = md.get("date_created")
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


def format_date(d: datetime) -> str:
    return d.strftime("%a, %d %b")  # Mon, 22 Dec


def limit(ids: List[str], n=6):
    return ids[:n]


@router.get("/")
async def get_memories():
    images = db_get_all_images()
    today = datetime.now()
    memories: List[Memory] = []

    # =====================================================
    # 1️ SPOTLIGHT (TODAY)
    # =====================================================
    spotlight_ids = []
    spotlight_date = None

    for img in images:
        d = parse_date(img)
        if not d:
            continue

        if d.date() == today.date():
            spotlight_ids.append(img["id"])
            spotlight_date = d

    if spotlight_ids:
        memories.append(
            Memory(
                id="spotlight-today",
                type="SPOTLIGHT",
                title="Spotlight of the day",
                subtitle=format_date(spotlight_date),
                image_ids=limit(spotlight_ids),
            )
        )

    # =====================================================
    # 2️ REVISIT THE MOMENT
    # =====================================================
    revisit_ids = []
    revisit_date = None

    for img in images:
        d = parse_date(img)
        if not d:
            continue

        if d.day == today.day and d.month == today.month and d.year < today.year:
            revisit_ids.append(img["id"])
            revisit_date = d

    if revisit_ids:
        memories.append(
            Memory(
                id="revisit",
                type="REVISIT",
                title="Revisit the moment",
                subtitle=format_date(revisit_date),
                image_ids=limit(revisit_ids),
            )
        )

    # =====================================================
    # 3️ WEEKEND MEMORIES
    # =====================================================
    weekend_ids = []

    for img in images:
        d = parse_date(img)
        if not d:
            continue

        if d.weekday() in (5, 6):  # Sat, Sun
            weekend_ids.append(img["id"])

    if len(weekend_ids) >= 2:
        memories.append(
            Memory(
                id="weekend",
                type="WEEKEND",
                title="Weekend memories",
                subtitle="Relaxed moments",
                image_ids=limit(weekend_ids),
            )
        )

    # =====================================================
    # 4️ YEAR MEMORIES (FIXED includes 2025)
    # =====================================================
    year_map: Dict[int, List[str]] = {}

    for img in images:
        d = parse_date(img)
        if not d:
            continue
        year_map.setdefault(d.year, []).append(img["id"])

    for year in sorted(year_map.keys(), reverse=True):
        ids = year_map[year]
        if len(ids) >= 2:
            memories.append(
                Memory(
                    id=f"year-{year}",
                    type="YEAR",
                    title=f"Memories from {year}",
                    subtitle=f"{len(ids)} photos",
                    image_ids=limit(ids),
                )
            )

    return {"success": True, "data": memories}
