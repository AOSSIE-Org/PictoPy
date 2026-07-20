"""Download the calibration eval set from Wikimedia Commons.

Reads scripts/vocabulary/eval_manifest.json and fetches images_per_label
images per entry into scripts/vocabulary/eval_images/ (gitignored), named
<label>__<n>.jpg. Idempotent: existing files are kept. Attribution URLs are
recorded in eval_images/attribution.json.

Run from the backend directory:  python scripts/build_eval_set.py
Stdlib-only, like build_semantic_vocabulary.py.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VOCAB_DIR = Path(__file__).resolve().parent / "vocabulary"
MANIFEST = VOCAB_DIR / "eval_manifest.json"
IMAGES_DIR = VOCAB_DIR / "eval_images"
ATTRIBUTION = IMAGES_DIR / "attribution.json"

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "PictoPy-eval-builder/0.1 (dev tooling; github.com/AOSSIE-Org/PictoPy)"
MIN_WIDTH = 500
THUMB_WIDTH = 640


# Commons' robot policy 429s sustained fast bursts; stay comfortably slow.
REQUEST_DELAY_S = 3.0


def _get(url: str) -> bytes:
    # polite pacing + backoff: Commons 429s on unthrottled request bursts
    for attempt in range(4):
        time.sleep(REQUEST_DELAY_S * (1 + attempt * 2))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 3:
                raise
    raise RuntimeError("unreachable")


def search_images(query: str, limit: int) -> list[dict]:
    """Search Commons bitmaps for query; returns imageinfo dicts by relevance."""
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrnamespace": 6,
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size",
            "iiurlwidth": THUMB_WIDTH,
        }
    )
    data = json.loads(_get(f"{API}?{params}"))
    pages = data.get("query", {}).get("pages", {})
    results = sorted(pages.values(), key=lambda p: p.get("index", 999))
    infos = []
    for page in results:
        info = (page.get("imageinfo") or [{}])[0]
        if info.get("width", 0) >= MIN_WIDTH and info.get("thumburl"):
            info["descriptionurl"] = info.get("descriptionurl", "")
            infos.append(info)
    return infos


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    per_label = manifest["images_per_label"]
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    attribution = (
        json.loads(ATTRIBUTION.read_text(encoding="utf-8"))
        if ATTRIBUTION.exists()
        else {}
    )

    downloaded = skipped = failed = 0
    for entry in manifest["entries"]:
        label = entry["label"]
        targets = [
            IMAGES_DIR / f"{label.replace(' ', '_')}__{i}.jpg" for i in range(per_label)
        ]
        if all(t.exists() for t in targets):
            skipped += per_label
            continue

        try:
            infos = search_images(entry["query"], per_label * 3)
        except Exception as e:
            print(f"search failed for {label!r}: {e}")
            failed += per_label
            continue

        # index-aligned pairing so a refill run doesn't re-download the
        # image an existing sibling slot already has
        for i, target in enumerate(targets):
            if target.exists() or i >= len(infos):
                continue
            info = infos[i]
            try:
                target.write_bytes(_get(info["thumburl"]))
                attribution[target.name] = info["descriptionurl"]
                downloaded += 1
                print(f"{target.name}  <-  {info['descriptionurl']}")
            except Exception as e:
                print(f"download failed for {label!r}: {e}")
                failed += 1

    ATTRIBUTION.write_text(
        json.dumps(attribution, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"\ndownloaded: {downloaded}, kept existing: {skipped}, failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
