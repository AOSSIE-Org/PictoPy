# from fastapi import APIRouter, HTTPException
# from typing import List, Dict, Any
# from datetime import datetime
# import math

# from app.database.images import db_get_all_images
# from app.utils.images import image_util_parse_metadata

# router = APIRouter()

# # -------------------------------------------------
# # Helpers
# # -------------------------------------------------

# def haversine_distance(lat1, lon1, lat2, lon2) -> float:
#     R = 6371
#     lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
#     dlat = lat2 - lat1
#     dlon = lon2 - lon1
#     a = (
#         math.sin(dlat / 2) ** 2
#         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
#     )
#     return 2 * R * math.asin(math.sqrt(a))


# def decide_memory_type(date: datetime, lat, lon) -> str:
#     now = datetime.now()

#     if date.month == now.month and date.day == now.day and date.year != now.year:
#         return "on_this_day"

#     if lat is not None and lon is not None:
#         return "trip"

#     return "date_range"


# def generate_title(date: datetime, lat, lon) -> str:
#     now = datetime.now()

#     if date.month == now.month and date.day == now.day and date.year != now.year:
#         years = now.year - date.year
#         return "On this day last year" if years == 1 else f"On this day {years} years ago"

#     if lat is not None and lon is not None:
#         return f"Trip from {date.strftime('%B %Y')}"

#     return f"Memories from {date.strftime('%B %Y')}"

# # -------------------------------------------------
# # Core Logic
# # -------------------------------------------------

# def group_images(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     memories: List[Dict[str, Any]] = []

#     for img in images:
#         metadata = img.get('metadata', {})
#         date_str = metadata.get("date_created")
#         lat = metadata.get("latitude")
#         lon = metadata.get("longitude")

#         if not date_str:
#             continue

#         try:
#             date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
#         except Exception:
#             continue

#         matched = None

#         for mem in memories:
#             # Time proximity
#             if abs((date - mem["anchor_date"]).days) <= 7:

#                 # GPS based grouping
#                 if lat is not None and lon is not None and mem["lat"] is not None:
#                     if haversine_distance(lat, lon, mem["lat"], mem["lon"]) <= 10:
#                         matched = mem
#                         break

#                 # No GPS → group by month
#                 elif lat is None and mem["lat"] is None:
#                     if date.month == mem["anchor_date"].month and date.year == mem["anchor_date"].year:
#                         matched = mem
#                         break

#         if not matched:
#             matched = {
#                 "memory_id": f"memory_{len(memories)}",
#                 "anchor_date": date,
#                 "date_range_start": date,
#                 "date_range_end": date,
#                 "lat": lat,
#                 "lon": lon,
#                 "images": [],
#             }
#             memories.append(matched)

#         matched["images"].append(img)
#         matched["date_range_start"] = min(matched["date_range_start"], date)
#         matched["date_range_end"] = max(matched["date_range_end"], date)

#     # -------------------------------------------------
#     # Final formatting
#     # -------------------------------------------------

#     result: List[Dict[str, Any]] = []

#     for mem in memories:
#         images_sorted = sorted(
#             mem["images"],
#             key=lambda i: i.get('metadata', {}).get("date_created") or ""
#         )

#         highlights = images_sorted[:5]

#         result.append({
#             "id": mem["memory_id"],
#             "title": generate_title(mem["anchor_date"], mem["lat"], mem["lon"]),
#             "date": mem["anchor_date"].isoformat(),
#             "images": highlights,
#             "lat": mem["lat"],
#             "lon": mem["lon"],
#         })

#     result.sort(key=lambda m: m["date"], reverse=True)
#     return result

# # -------------------------------------------------
# # API
# # -------------------------------------------------

# @router.get("/")
# def get_memories():
#     try:
#         images = db_get_all_images()
#         return {
#             "success": True,
#             "data": group_images(images)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import math

from app.database.images import db_get_all_images

router = APIRouter()

# -------------------------------------------------
# Helpers
# -------------------------------------------------


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def decide_memory_type(mem: Dict[str, Any]) -> str:
    now = datetime.now()
    date = mem["anchor_date"]
    lat = mem["lat"]
    lon = mem["lon"]

    if date.month == now.month and date.day == now.day and date.year != now.year:
        return "on_this_day"

    if lat is not None and lon is not None:
        return "trip"

    return "date_range"


def generate_title(mem: Dict[str, Any]) -> str:
    mtype = decide_memory_type(mem)
    date = mem["anchor_date"]
    now = datetime.now()

    if mtype == "on_this_day":
        years = now.year - date.year
        return (
            "On this day last year"
            if years == 1
            else f"On this day · {years} years ago"
        )

    if mtype == "trip":
        return f"Trip · {date.strftime('%B %Y')}"

    return f"Memories from {date.strftime('%B %Y')}"


# -------------------------------------------------
# Core Logic
# -------------------------------------------------


def group_images(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    memories: List[Dict[str, Any]] = []

    for img in images:
        metadata = img.get("metadata", {})
        date_str = metadata.get("date_created")
        lat = metadata.get("latitude")
        lon = metadata.get("longitude")

        if not date_str:
            continue

        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            continue

        matched = None

        for mem in memories:
            # time window: ±3 days
            if abs((date - mem["anchor_date"]).days) <= 3:

                # GPS based trip
                if (
                    lat is not None
                    and lon is not None
                    and mem["lat"] is not None
                    and mem["lon"] is not None
                ):
                    if haversine_distance(lat, lon, mem["lat"], mem["lon"]) <= 10:
                        matched = mem
                        break

                # no GPS → same month grouping
                for mem in memories:
                    day_diff = abs((date - mem["anchor_date"]).days)

                # 1️⃣ Same-day / near-day memory
                if day_diff <= 1:
                    matched = mem
                break

                # 2️⃣ Trip memory (GPS + time)
                if (
                    lat is not None
                    and lon is not None
                    and mem["lat"] is not None
                    and mem["lon"] is not None
                    and day_diff <= 3
                    and haversine_distance(lat, lon, mem["lat"], mem["lon"]) <= 10
                ):
                    matched = mem
                    break

        if not matched:
            matched = {
                "memory_id": f"memory_{len(memories)}",
                "anchor_date": date,
                "date_range_start": date,
                "date_range_end": date,
                "lat": lat,
                "lon": lon,
                "images": [],
            }
            memories.append(matched)

        matched["images"].append(img)
        matched["date_range_start"] = min(matched["date_range_start"], date)
        matched["date_range_end"] = max(matched["date_range_end"], date)

    # -------------------------------------------------
    # Final formatting (IMPORTANT)
    # -------------------------------------------------

    result: List[Dict[str, Any]] = []

    for mem in memories:
        # ❗ Google Photos rule: at least 2 images
        if len(mem["images"]) < 2:
            continue

        images_sorted = sorted(
            mem["images"], key=lambda i: i.get("metadata", {}).get("date_created") or ""
        )

        highlights = images_sorted[:5]
        cover = highlights[0]

        result.append(
            {
                "id": mem["memory_id"],
                "title": generate_title(mem),
                "memory_type": decide_memory_type(mem),
                "date_range_start": mem["date_range_start"].isoformat(),
                "date_range_end": mem["date_range_end"].isoformat(),
                "image_count": len(mem["images"]),
                "representative_image": {
                    "id": cover["id"],
                    "thumbnailPath": cover["thumbnailPath"],
                    "metadata": cover["metadata"],
                },
                "images": mem["images"],
            }
        )

    result.sort(key=lambda m: m["date_range_start"], reverse=True)
    return result


# -------------------------------------------------
# API
# -------------------------------------------------


@router.get("/")
def get_memories():
    try:
        images = db_get_all_images()
        return {
            "success": True,
            "data": group_images(images),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}/images")
def get_memory_images(memory_id: str):
    try:
        images = db_get_all_images()
        grouped_memories = group_images(images)

        for mem in grouped_memories:
            if mem["id"] == memory_id:
                return {
                    "success": True,
                    "data": mem["images"],
                }

        raise HTTPException(status_code=404, detail="Memory not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
