from __future__ import annotations

from typing import TYPE_CHECKING

from app.logging.setup_logging import get_logger

if TYPE_CHECKING:
    import numpy as np

logger = get_logger(__name__)

SCORING_CHUNK_SIZE = 256


def _scoring_signature(
    model_version: str,
    top_k: int,
    thresholds: np.ndarray,
    meta: list[tuple[int, str, float | None]],
    label_matrix: np.ndarray,
) -> str:
    """Fingerprint of everything an image's stored scores depend on. Any
    change (vocabulary, label embeddings, thresholds, K, checkpoint) makes
    every image look unscored, and the sweep rewrites it -- re-scoring is one
    matmul, so wholesale invalidation is cheaper than tracking deltas."""
    import hashlib

    h = hashlib.sha256()
    h.update(f"{model_version}|k={top_k}".encode())
    for (class_id, category, _), threshold in zip(meta, thresholds):
        h.update(f"|{class_id}:{category}:{threshold:g}".encode())
    h.update(label_matrix.tobytes())
    return h.hexdigest()[:16]


def semantic_util_sync_vocabulary() -> None:
    """Sync the shipped seed vocabulary file into the database.

    Runs at startup after the mappings table exists; idempotent and cheap.
    """
    import json
    from pathlib import Path
    from app.database.semantic_labels import db_upsert_semantic_vocabulary

    seed_path = (
        Path(__file__).resolve().parents[1] / "data" / "semantic_vocabulary.json"
    )
    try:
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        db_upsert_semantic_vocabulary(seed["labels"])
    except Exception as e:
        logger.error(f"Failed to sync semantic vocabulary: {e}")


def semantic_util_build_label_embeddings() -> None:
    """Build cached label embeddings for the active checkpoint.

    Self-gating and idempotent: skips when the text model isn't installed,
    and only encodes labels whose cache is missing or stale (over-triggering
    is a cheap no-op). A label's embedding is the renormalized mean of its
    description embeddings (prompt ensembling).
    """
    import os
    import time
    import numpy as np
    from app.config.settings import (
        SIGLIP2_ACTIVE_CHECKPOINT,
        SIGLIP2_SCORING_METADATA,
    )
    from app.models.model_registry import (
        get_siglip2_registry_keys,
        get_siglip2_tokenizer_key,
        get_model_path,
    )
    from app.database.semantic_labels import (
        db_get_labels_needing_embeddings,
        db_update_label_embeddings,
    )

    try:
        _, text_key = get_siglip2_registry_keys(SIGLIP2_ACTIVE_CHECKPOINT)
        tokenizer_key = get_siglip2_tokenizer_key(SIGLIP2_ACTIVE_CHECKPOINT)
        text_model_path = get_model_path(text_key)
        tokenizer_path = get_model_path(tokenizer_key)
        if not os.path.exists(text_model_path) or not os.path.exists(tokenizer_path):
            logger.info(
                "SigLIP2 text model/tokenizer not installed; "
                "skipping label embedding build"
            )
            return

        metadata = SIGLIP2_SCORING_METADATA[SIGLIP2_ACTIVE_CHECKPOINT]
        model_version = metadata["model_version"]

        stale = db_get_labels_needing_embeddings(model_version)
        if not stale:
            return

        from app.utils.SigLIP import (
            siglip_util_tokenize_query,
            siglip_util_get_text_model,
        )

        text_model = siglip_util_get_text_model(text_model_path, text_key)
        start_time = time.time()

        rows = []
        for class_id, descriptions in stale:
            # Descriptions are caption-shaped already; encoded as-is, no
            # SIGLIP2_QUERY_TEMPLATE wrapping (that template exists to fix
            # bare-noun live queries).
            vectors = []
            for description in descriptions:
                input_ids, attention_mask = siglip_util_tokenize_query(description)
                embedding = text_model.get_embedding(input_ids, attention_mask)
                vectors.append(np.asarray(embedding, dtype=np.float32).flatten())
            mean = np.mean(vectors, axis=0)
            norm = np.linalg.norm(mean)
            rows.append((class_id, mean / norm if norm > 0 else mean, model_version))

        db_update_label_embeddings(rows)
        elapsed = time.time() - start_time
        logger.info(
            f"Label embedding build complete. Labels: {len(rows)}, "
            f"Elapsed: {elapsed:.2f}s"
        )
    except Exception as e:
        logger.error(f"Error building semantic label embeddings: {e}")


def semantic_util_score_images() -> None:
    """Score embedded images against the cached label matrix and write
    top-K above-threshold tags as image_classes rows.

    Self-gating and idempotent: needs only cached embeddings (no models),
    skips images already scored against the current scoring signature. Runs
    after the embedding pass and whenever the vocabulary or label
    embeddings change.
    """
    import time
    import numpy as np
    from app.config.settings import (
        SIGLIP2_ACTIVE_CHECKPOINT,
        SIGLIP2_SCORING_METADATA,
        SEMANTIC_SCORE_TOP_K,
        SEMANTIC_BUCKET_THRESHOLDS,
        SEMANTIC_DEFAULT_THRESHOLD,
    )
    from app.database.semantic_labels import (
        db_get_active_label_embeddings,
        db_write_image_semantic_scores,
    )
    from app.database.image_embeddings import db_get_embeddings_needing_scoring

    try:
        metadata = SIGLIP2_SCORING_METADATA[SIGLIP2_ACTIVE_CHECKPOINT]
        model_version = metadata["model_version"]
        logit_scale = np.exp(metadata["logit_scale"])
        logit_bias = metadata["logit_bias"]

        meta, label_matrix = db_get_active_label_embeddings(model_version)
        if not meta:
            logger.info(
                "No cached label embeddings for the active checkpoint; "
                "skipping semantic scoring pass"
            )
            return

        thresholds = np.array(
            [
                (
                    override
                    if override is not None
                    else SEMANTIC_BUCKET_THRESHOLDS.get(
                        category, SEMANTIC_DEFAULT_THRESHOLD
                    )
                )
                for _, category, override in meta
            ],
            dtype=np.float32,
        )
        signature = _scoring_signature(
            model_version, SEMANTIC_SCORE_TOP_K, thresholds, meta, label_matrix
        )

        total_images = 0
        start_time = time.time()
        while True:
            image_ids, image_matrix = db_get_embeddings_needing_scoring(
                model_version, signature, SCORING_CHUNK_SIZE
            )
            if not image_ids:
                break

            logits = image_matrix @ label_matrix.T * logit_scale + logit_bias
            scores = 1.0 / (1.0 + np.exp(-logits))

            batch = []
            for i, image_id in enumerate(image_ids):
                row = scores[i]
                candidates = np.flatnonzero(row >= thresholds)
                if len(candidates) > SEMANTIC_SCORE_TOP_K:
                    keep = np.argsort(row[candidates])[::-1][:SEMANTIC_SCORE_TOP_K]
                    candidates = candidates[keep]
                batch.append(
                    (
                        image_id,
                        [(meta[j][0], float(row[j])) for j in candidates],
                    )
                )

            db_write_image_semantic_scores(batch, signature)
            total_images += len(image_ids)

        if total_images:
            elapsed = time.time() - start_time
            logger.info(
                f"Semantic scoring pass complete. Images: {total_images}, "
                f"Labels: {len(meta)}, Elapsed: {elapsed:.2f}s"
            )
    except Exception as e:
        logger.error(f"Error in semantic scoring pass: {e}")
