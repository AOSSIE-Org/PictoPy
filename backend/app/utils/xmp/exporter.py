import os
from typing import Dict, List, Optional, TypedDict

from app.database.metadata import db_get_metadata
from app.database.xmp_export_state import (
    XmpExportCandidate,
    db_get_xmp_export_candidates,
    db_record_xmp_export_failure,
    db_record_xmp_export_success,
    db_refresh_image_file_stat,
)
from app.logging.setup_logging import get_logger
from app.schemas.user_preferences import UserPreferencesData

from .collector import collect_image_metadata
from .schema import PictoPyMetadata
from .service import WriteOutcome, metadata_digest, write_image_metadata

logger = get_logger(__name__)

# Images collected from the database per round; bounds memory on big libraries.
EXPORT_BATCH_SIZE = 200

# Recorded for images with nothing worth writing that were never written.
OUTCOME_EMPTY = "empty"


class ExportSummary(TypedDict):
    checked: int
    written: int
    unchanged: int
    # Nothing to write: no PictoPy data to store, or an unsupported format.
    skipped: int
    # Not written on purpose: unreadable existing XMP, or a newer PictoPy's data.
    left_alone: int
    failed: int


def _empty_summary() -> ExportSummary:
    return {
        "checked": 0,
        "written": 0,
        "unchanged": 0,
        "skipped": 0,
        "left_alone": 0,
        "failed": 0,
    }


# Files the export deliberately leaves untouched rather than overwrite.
_LEFT_ALONE = (WriteOutcome.UNREADABLE_EXISTING, WriteOutcome.NEWER_SCHEMA)


def xmp_export_enabled() -> bool:
    stored = (db_get_metadata() or {}).get("user_preferences") or {}
    try:
        return UserPreferencesData.model_validate(stored).Metadata_Export
    except ValueError:
        return False


def _file_unchanged(candidate: XmpExportCandidate) -> bool:
    if candidate["file_size"] is None or candidate["file_mtime_ns"] is None:
        return False
    try:
        stat = os.stat(candidate["path"])
    except OSError:
        return False
    return (stat.st_size, stat.st_mtime_ns) == (
        candidate["file_size"],
        candidate["file_mtime_ns"],
    )


def _has_content(metadata: PictoPyMetadata) -> bool:
    return bool(
        metadata.tags
        or metadata.semantic_tags
        or metadata.faces
        or metadata.image_embedding
        or metadata.albums
        or metadata.favourite
    )


def _export_one(
    candidate: XmpExportCandidate, metadata: PictoPyMetadata, summary: ExportSummary
) -> None:
    image_id, path = candidate["image_id"], candidate["path"]
    seen = candidate["change_count"]
    digest = metadata_digest(metadata)

    # The database already says this file holds exactly this data.
    if digest == candidate["digest"] and _file_unchanged(candidate):
        db_record_xmp_export_success(
            image_id,
            seen,
            WriteOutcome.UNCHANGED.value,
            digest,
            candidate["file_size"],
            candidate["file_mtime_ns"],
        )
        summary["unchanged"] += 1
        return

    # Touching a file only to store "nothing" would change it for no benefit.
    if candidate["digest"] is None and not _has_content(metadata):
        db_record_xmp_export_success(image_id, seen, OUTCOME_EMPTY, None, None, None)
        summary["skipped"] += 1
        return

    # Unreachable (unplugged drive, no permission) must fail and be retried;
    # the container check alone would call it unsupported and give up.
    with open(path, "rb"):
        pass
    outcome = write_image_metadata(path, metadata)
    if outcome in (WriteOutcome.WRITTEN, WriteOutcome.UNCHANGED):
        stat = os.stat(path)
        db_record_xmp_export_success(
            image_id, seen, outcome.value, digest, stat.st_size, stat.st_mtime_ns
        )
        if outcome is WriteOutcome.WRITTEN:
            # The write kept mtime but changed the size; without this the
            # folder rescan would treat the file as edited.
            db_refresh_image_file_stat(image_id, stat.st_size, int(stat.st_mtime))
            summary["written"] += 1
        else:
            summary["unchanged"] += 1
    else:
        # Not retried until the image changes again; a manual run rechecks.
        db_record_xmp_export_success(image_id, seen, outcome.value, None, None, None)
        summary["left_alone" if outcome in _LEFT_ALONE else "skipped"] += 1


def xmp_export_run(include_clean: bool = False) -> ExportSummary:
    """Write PictoPy's data into every PNG whose export is pending.

    include_clean, used by the manual export, recomputes every PNG instead,
    so a codec or schema change reaches files exported before it. Each image
    still goes through the same digest and stat check, so a file already
    holding the current data is not opened. A failure is recorded per image
    and never stops the pass.
    """
    summary = _empty_summary()
    candidates = db_get_xmp_export_candidates(include_clean)
    for start in range(0, len(candidates), EXPORT_BATCH_SIZE):
        batch: List[XmpExportCandidate] = candidates[start : start + EXPORT_BATCH_SIZE]

        metadata: Dict[str, PictoPyMetadata] = collect_image_metadata(
            [c["image_id"] for c in batch]
        )
        for candidate in batch:
            image_metadata = metadata.get(candidate["image_id"])
            if image_metadata is None:
                continue  # deleted since the candidates were listed
            summary["checked"] += 1
            try:
                _export_one(candidate, image_metadata, summary)
            except Exception as e:
                summary["failed"] += 1
                error = f"{type(e).__name__}: {e}"
                db_record_xmp_export_failure(candidate["image_id"], error)
                # Every pass retries, so a file that keeps failing (read-only
                # folder) is reported once rather than on every sync.
                log = logger.debug if candidate["failure_count"] else logger.warning
                log(f"Metadata export failed for {candidate['path']}: {error}")

    if summary["written"] or summary["failed"]:
        logger.info(f"Metadata export: {summary}")
    return summary


def xmp_export_if_enabled() -> Optional[ExportSummary]:
    """The automatic pass: runs only while the Settings toggle is on."""
    if not xmp_export_enabled():
        return None
    return xmp_export_run()
