"""Derivation script for the semantic vocabulary seed (curated-vocabulary layer, step 1).

Pulls the Places365 scene categories and Open Images boxable class list,
applies the mechanical prune rules (COCO-80 exclusion, person/body-part
exclusion, cross-source dedupe), and emits a raw candidate list for the
hand-prune pass.

Run from the backend directory:  python scripts/build_semantic_vocabulary.py

Output:  scripts/vocabulary/raw_candidates.json  (committed, reviewable)
Source downloads are cached in  scripts/vocabulary/sources/  (gitignored).

Stdlib-only on purpose: the COCO class list is read out of app/utils/YOLO.py
via ast instead of importing it, so this runs without the backend's ML deps.
"""

from __future__ import annotations

import ast
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
YOLO_SOURCE = BACKEND_DIR / "app" / "utils" / "YOLO.py"
OUTPUT_DIR = Path(__file__).resolve().parent / "vocabulary"
SOURCES_DIR = OUTPUT_DIR / "sources"
OUTPUT_FILE = OUTPUT_DIR / "raw_candidates.json"

PLACES365_URL = (
    "https://raw.githubusercontent.com/CSAILVision/places365/master/"
    "categories_places365.txt"
)
OPEN_IMAGES_URL = (
    "https://storage.googleapis.com/openimages/v7/"
    "oidv7-class-descriptions-boxable.csv"
)

# COCO name -> Open Images display names for the same concept. Exact-name and
# naive plural matching catch the rest; hand-prune is the backstop for subtypes.
COCO_TO_OPEN_IMAGES_ALIASES: dict[str, list[str]] = {
    "tv": ["television"],
    "cell phone": ["mobile phone"],
    "remote": ["remote control"],
    "mouse": ["computer mouse"],
    "keyboard": ["computer keyboard"],
    "microwave": ["microwave oven"],
    "donut": ["doughnut"],
    "hair drier": ["hair dryer"],
    "potted plant": ["houseplant"],
    "couch": ["sofa bed"],
    "cow": ["cattle"],
    "frisbee": ["flying disc"],
    "skis": ["ski"],
    "sports ball": ["ball"],
    "dining table": ["kitchen & dining room table"],
    "airplane": ["aeroplane"],
    "motorcycle": ["motorbike"],
}

# Person concepts are owned by YOLO ("person") + the face pipeline. Open Images
# body-part labels ("Human face", "Human arm", ...) are dropped by prefix below.
PERSON_LABELS = {"person", "human", "man", "woman", "boy", "girl"}


def load_coco_class_names() -> list[str]:
    """Read class_names from app/utils/YOLO.py without importing it."""
    tree = ast.parse(YOLO_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "class_names":
                    names = ast.literal_eval(node.value)
                    if not (isinstance(names, list) and len(names) == 80):
                        raise ValueError(
                            f"class_names in {YOLO_SOURCE} is not the expected "
                            f"80-entry list (got {len(names)})"
                        )
                    return names
    raise ValueError(f"class_names assignment not found in {YOLO_SOURCE}")


def fetch_cached(url: str, cache_path: Path) -> str:
    """Download url to cache_path unless already cached; return its text."""
    if cache_path.exists():
        print(f"using cached {cache_path.name}")
    else:
        print(f"downloading {url}")
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
    return cache_path.read_text(encoding="utf-8")


def normalize(name: str) -> str:
    return " ".join(name.strip().lower().replace("_", " ").split())


def parse_places365(text: str) -> dict[str, list[str]]:
    """Parse categories_places365.txt into {base name: [qualifiers]}.

    Lines look like '/a/apartment_building/outdoor 0' -- the leading letter is
    an index bucket, and a trailing path segment ('outdoor', 'sand', ...) is a
    qualifier of the same base scene, merged here and kept as a variant note.
    """
    merged: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        path = line.split()[0]
        parts = [p for p in path.split("/") if p]
        # parts[0] is the one-letter bucket; parts[1] the category name
        base = normalize(parts[1])
        qualifiers = [normalize(p) for p in parts[2:]]
        merged.setdefault(base, [])
        for q in qualifiers:
            if q not in merged[base]:
                merged[base].append(q)
    return merged


def parse_open_images(text: str) -> list[str]:
    """Parse oidv7-class-descriptions-boxable.csv into display names."""
    names = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if len(row) < 2 or not row[0].startswith("/m/"):
            continue  # header or malformed line
        names.append(normalize(row[1]))
    return names


def build_exclusion_set(coco_names: list[str]) -> set[str]:
    excluded = set(PERSON_LABELS)
    for name in coco_names:
        norm = normalize(name)
        excluded.add(norm)
        for alias in COCO_TO_OPEN_IMAGES_ALIASES.get(norm, []):
            excluded.add(normalize(alias))
    return excluded


def is_excluded(name: str, exclusion: set[str]) -> bool:
    if name in exclusion:
        return True
    # naive plural/singular bridging: "cars" vs "car", "boxes" vs "box"
    if name + "s" in exclusion or name + "es" in exclusion:
        return True
    if name.endswith("es") and name[:-2] in exclusion:
        return True
    if name.endswith("s") and name[:-1] in exclusion:
        return True
    # Open Images body-part labels ("human face", "human arm", ...)
    if name.startswith("human "):
        return True
    return False


def main() -> int:
    coco_names = load_coco_class_names()
    exclusion = build_exclusion_set(coco_names)

    places_raw = parse_places365(
        fetch_cached(PLACES365_URL, SOURCES_DIR / "categories_places365.txt")
    )
    open_images_raw = parse_open_images(
        fetch_cached(
            OPEN_IMAGES_URL, SOURCES_DIR / "oidv7-class-descriptions-boxable.csv"
        )
    )

    candidates: dict[str, dict] = {}
    excluded_counts = {"places365": 0, "open_images": 0}

    for name, variants in places_raw.items():
        if is_excluded(name, exclusion):
            excluded_counts["places365"] += 1
            continue
        entry = {"name": name, "category": "scene", "sources": ["places365"]}
        if variants:
            entry["variants"] = variants
        candidates[name] = entry

    for name in open_images_raw:
        if is_excluded(name, exclusion):
            excluded_counts["open_images"] += 1
            continue
        if name in candidates:
            # already present from Places365; scene category wins, record source
            if "open_images" not in candidates[name]["sources"]:
                candidates[name]["sources"].append("open_images")
            continue
        candidates[name] = {
            "name": name,
            "category": "object",
            "sources": ["open_images"],
        }

    ordered = sorted(candidates.values(), key=lambda e: e["name"])
    output = {
        "generated_by": "scripts/build_semantic_vocabulary.py",
        "sources": {
            "places365": PLACES365_URL,
            "open_images": OPEN_IMAGES_URL,
            "coco_exclusion": "app/utils/YOLO.py class_names",
        },
        "candidate_count": len(ordered),
        "candidates": ordered,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    both = sum(1 for e in ordered if len(e["sources"]) == 2)
    print(
        f"places365: {len(places_raw)} base scenes "
        f"({excluded_counts['places365']} excluded)"
    )
    print(
        f"open_images: {len(open_images_raw)} boxable classes "
        f"({excluded_counts['open_images']} excluded)"
    )
    print(f"candidates: {len(ordered)} ({both} present in both sources)")
    print(f"wrote {OUTPUT_FILE.relative_to(BACKEND_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
