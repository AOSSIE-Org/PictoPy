"""Bucket calibration for the semantic vocabulary (offline dev script).

Scores the eval set (scripts/vocabulary/eval_images/, built by
build_eval_set.py) against the full seed vocabulary through the production
pipeline: siglip_util_preprocess_image -> SigLIP2Vision, descriptions ->
SigLIP2Text ensembled label vectors, calibrated sigmoid scores.

Reports, per category bucket:
  - ground-truth (positive) and non-ground-truth (negative) score percentiles
  - ground-truth rank stats (top-1/5/10/15 over all labels)
  - a threshold sweep: recall vs mean labels-per-image (tag spam)
  - null-baseline margin analysis (score minus a generic-prompt baseline)

Writes scripts/vocabulary/calibration_report.json.
Requires the backend environment + installed SigLIP2 models.
Run from the backend directory:  python scripts/calibrate_semantic_vocabulary.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

VOCAB_DIR = Path(__file__).resolve().parent / "vocabulary"
IMAGES_DIR = VOCAB_DIR / "eval_images"
SEED = (
    Path(__file__).resolve().parent.parent / "app" / "data" / "semantic_vocabulary.json"
)
REPORT = VOCAB_DIR / "calibration_report.json"

GENERIC_PROMPTS = [
    "a photo",
    "an image of something",
    "a picture",
    "a snapshot of a scene",
]

THRESHOLDS = [0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02]
MARGIN_FACTORS = [1.0, 2.0, 5.0, 10.0, 25.0]  # score >= factor * generic baseline


def build_label_matrix(
    labels: list[dict],
    text_model: Any,
    tokenize: Callable[[str], tuple[np.ndarray, np.ndarray]],
) -> np.ndarray:
    """Ensembled label vectors: renormalized mean of description embeddings."""
    vectors = []
    for label in labels:
        per_desc = []
        for description in label["descriptions"]:
            input_ids, attention_mask = tokenize(description)
            emb = text_model.get_embedding(input_ids, attention_mask)
            per_desc.append(np.asarray(emb, dtype=np.float32).flatten())
        mean = np.mean(per_desc, axis=0)
        norm = np.linalg.norm(mean)
        vectors.append(mean / norm if norm > 0 else mean)
    return np.vstack(vectors)


def main() -> int:
    from app.config.settings import (
        SIGLIP2_ACTIVE_CHECKPOINT,
        SIGLIP2_SCORING_METADATA,
    )
    from app.models.model_registry import get_siglip2_registry_keys, get_model_path
    from app.models.SigLIP2Vision import SigLIP2Vision
    from app.models.SigLIP2Text import SigLIP2Text
    from app.utils.SigLIP import (
        siglip_util_preprocess_image,
        siglip_util_tokenize_query,
    )

    metadata = SIGLIP2_SCORING_METADATA[SIGLIP2_ACTIVE_CHECKPOINT]
    resolution = metadata["input_resolution"]
    logit_scale = np.exp(metadata["logit_scale"])
    logit_bias = metadata["logit_bias"]

    seed = json.loads(SEED.read_text(encoding="utf-8"))
    labels = seed["labels"]
    name_to_idx = {e["name"]: i for i, e in enumerate(labels)}
    categories = [e["category"] for e in labels]

    eval_files = sorted(IMAGES_DIR.glob("*__*.jpg"))
    if not eval_files:
        print(f"no eval images in {IMAGES_DIR}; run build_eval_set.py first")
        return 1

    vision_key, text_key = get_siglip2_registry_keys(SIGLIP2_ACTIVE_CHECKPOINT)

    print(f"encoding {len(labels)} labels...")
    start = time.time()
    text_model = SigLIP2Text(get_model_path(text_key))
    try:
        label_matrix = build_label_matrix(
            labels, text_model, siglip_util_tokenize_query
        )
        generic_vecs = []
        for prompt in GENERIC_PROMPTS:
            input_ids, attention_mask = siglip_util_tokenize_query(prompt)
            emb = text_model.get_embedding(input_ids, attention_mask)
            generic_vecs.append(np.asarray(emb, dtype=np.float32).flatten())
        generic_matrix = np.vstack(generic_vecs)
    finally:
        text_model.close()
    print(f"  {time.time() - start:.1f}s")

    print(f"embedding {len(eval_files)} eval images...")
    start = time.time()
    vision = SigLIP2Vision(get_model_path(vision_key))
    image_vecs, gt_indices, kept_files = [], [], []
    try:
        for path in eval_files:
            gt_name = path.stem.split("__")[0].replace("_", " ")
            if gt_name not in name_to_idx:
                print(f"  skipping {path.name}: no vocabulary label {gt_name!r}")
                continue
            arr = siglip_util_preprocess_image(str(path), resolution)
            if arr is None:
                print(f"  skipping {path.name}: unreadable")
                continue
            image_vecs.append(vision.get_embedding(np.stack([arr]))[0])
            gt_indices.append(name_to_idx[gt_name])
            kept_files.append(path.name)
    finally:
        vision.close()
    print(f"  {time.time() - start:.1f}s")

    images = np.vstack(image_vecs)  # [I, D]
    gt = np.array(gt_indices)

    def sigmoid_scores(text_matrix):
        logits = images @ text_matrix.T * logit_scale + logit_bias
        return 1.0 / (1.0 + np.exp(-logits))

    scores = sigmoid_scores(label_matrix)  # [I, N]
    generic = sigmoid_scores(generic_matrix).mean(axis=1)  # [I]

    n_images, n_labels = scores.shape
    gt_scores = scores[np.arange(n_images), gt]
    ranks = (scores > gt_scores[:, None]).sum(axis=1) + 1  # 1-based GT rank

    report = {"checkpoint": metadata["model_version"], "buckets": {}}
    pct = [10, 25, 50, 75, 90]

    for bucket in ("scene", "object", "event", "attribute"):
        mask = np.array([categories[g] == bucket for g in gt])
        if not mask.any():
            continue
        b_scores = scores[mask]
        b_gt = gt_scores[mask]
        b_ranks = ranks[mask]
        neg = b_scores.copy()
        neg[np.arange(mask.sum()), gt[mask]] = np.nan
        neg = neg[~np.isnan(neg)]

        sweep = []
        for t in THRESHOLDS:
            sweep.append(
                {
                    "threshold": t,
                    "recall": float((b_gt >= t).mean()),
                    "labels_per_image": float((b_scores >= t).sum(axis=1).mean()),
                }
            )

        margin_sweep = []
        b_generic = generic[mask]
        for f in MARGIN_FACTORS:
            above = b_scores >= (b_generic[:, None] * f)
            margin_sweep.append(
                {
                    "factor": f,
                    "recall": float(above[np.arange(mask.sum()), gt[mask]].mean()),
                    "labels_per_image": float(above.sum(axis=1).mean()),
                }
            )

        report["buckets"][bucket] = {
            "images": int(mask.sum()),
            "gt_score_percentiles": {
                f"p{p}": float(np.percentile(b_gt, p)) for p in pct
            },
            "neg_score_percentiles": {
                f"p{p}": float(np.percentile(neg, p)) for p in [50, 90, 99]
            },
            "gt_rank": {
                "top1": float((b_ranks <= 1).mean()),
                "top5": float((b_ranks <= 5).mean()),
                "top10": float((b_ranks <= 10).mean()),
                "top15": float((b_ranks <= 15).mean()),
                "median_rank": float(np.median(b_ranks)),
            },
            "threshold_sweep": sweep,
            "generic_baseline_margin_sweep": margin_sweep,
        }

    # worst-ranked eval images: bad descriptions or bad eval ground truth
    worst = np.argsort(ranks)[::-1][:15]
    report["worst_ranked_images"] = [
        {
            "file": kept_files[i],
            "gt_rank": int(ranks[i]),
            "gt_score": float(gt_scores[i]),
            "top_labels": [labels[j]["name"] for j in np.argsort(scores[i])[::-1][:5]],
        }
        for i in worst
    ]

    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"\n{'bucket':<10} {'imgs':>4} {'GT p50':>9} {'neg p99':>9} "
        f"{'top1':>6} {'top5':>6} {'top15':>6} {'med rank':>8}"
    )
    for bucket, b in report["buckets"].items():
        print(
            f"{bucket:<10} {b['images']:>4} "
            f"{b['gt_score_percentiles']['p50']:>9.6f} "
            f"{b['neg_score_percentiles']['p99']:>9.6f} "
            f"{b['gt_rank']['top1']:>6.2f} {b['gt_rank']['top5']:>6.2f} "
            f"{b['gt_rank']['top15']:>6.2f} {b['gt_rank']['median_rank']:>8.1f}"
        )
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
