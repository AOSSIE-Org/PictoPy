"""Benchmark for the face-clustering distance graph (offline dev script).

Measures the stage that used to blow up on large libraries -- building the
pairwise distance graph and running DBSCAN -- on synthetic embeddings with
known identities. Reports wall time, process peak RSS (the number the OOM
reports quote), the number of edges handed to DBSCAN, and clustering accuracy
(adjusted Rand index) against the ground-truth identities.

Two modes:

  dense   the old path: full float64 cosine matrix, exact kNN eps estimate
  sparse  the current path: radius neighbour graph, sampled eps estimate

Peak RSS only ever rises within a process, so each measurement runs in its own
subprocess and reports its own peak.

Run from the backend directory, in the backend environment:

    python scripts/benchmark_face_clustering.py
    python scripts/benchmark_face_clustering.py --sizes 1000,5000,10000
    python scripts/benchmark_face_clustering.py --modes dense,sparse --people 50
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sklearn import config_context
from sklearn.cluster import DBSCAN
from sklearn.metrics import adjusted_rand_score
from sklearn.metrics.pairwise import cosine_distances
from sklearn.neighbors import NearestNeighbors

import app.utils.face_clusters as fc

TIGHT = 0.02  # within-person spread; wider spreads make every eps estimate noisy


def _synthetic(
    size: int, people: int, dim: int, strangers: int, tight: float, seed: int
):
    """Tight identity blobs plus a few unclusterable strangers."""
    rng = np.random.default_rng(seed)
    centres = rng.normal(size=(people, dim))
    centres /= np.linalg.norm(centres, axis=1, keepdims=True)

    per_person = max(size - strangers, 1) // people
    rows: list[np.ndarray] = []
    truth: list[int] = []
    for person_id, centre in enumerate(centres):
        block = centre + rng.normal(scale=tight / np.sqrt(dim), size=(per_person, dim))
        block /= np.linalg.norm(block, axis=1, keepdims=True)
        rows.append(block)
        truth.extend([person_id] * per_person)
    for _ in range(strangers):
        stranger = rng.normal(size=dim)
        rows.append(stranger / np.linalg.norm(stranger))
        truth.append(-1)

    return np.vstack(rows).astype(np.float32), np.array(truth)


def _sparse_graph(embeddings: np.ndarray, max_distance: float):
    neighbours = NearestNeighbors(metric="cosine", n_jobs=-1).fit(embeddings)
    with config_context(working_memory=fc._KNN_WORKING_MEMORY_MB):
        return neighbours.radius_neighbors_graph(
            embeddings, radius=max_distance, mode="distance"
        )


def _dense_graph(embeddings: np.ndarray, max_distance: float) -> np.ndarray:
    """The old path: N x N float64, everything past max_distance pinned to 1.0."""
    distances = cosine_distances(embeddings).astype(np.float64)
    distances[distances > max_distance] = 1.0
    np.fill_diagonal(distances, 0.0)
    return distances


def _dense_estimate_eps(embeddings: np.ndarray, k: int) -> float:
    """The old eps estimate: exact 90th percentile over every face."""
    neighbours = NearestNeighbors(n_neighbors=k + 1, metric="cosine")
    neighbours.fit(embeddings)
    distances, _ = neighbours.kneighbors(embeddings)
    kth = distances[:, -1]
    kth.sort()
    return float(np.percentile(kth, 90))


def _build_graph(mode: str, embeddings: np.ndarray, max_distance: float):
    if mode == "dense":
        return _dense_graph(embeddings, max_distance)
    return _sparse_graph(embeddings, max_distance)


def _estimate_eps(mode: str, embeddings: np.ndarray, min_samples: int):
    if mode == "dense":
        return _dense_estimate_eps(embeddings, min_samples)
    return fc.estimate_eps(embeddings, k=min_samples)


def _partition(labels: np.ndarray):
    groups: dict[int, list[int]] = {}
    for index, label in enumerate(labels):
        groups.setdefault(int(label), []).append(index)
    return sorted(tuple(members) for members in groups.values())


def _peak_mib():
    if fc.resource is None:
        return None
    rss = fc.resource.getrusage(fc.resource.RUSAGE_SELF).ru_maxrss
    return rss / 1024 if sys.platform != "darwin" else rss / (1024 * 1024)


def _measure(mode: str, size: int, people: int, dim: int, strangers: int, seed: int):
    embeddings, truth = _synthetic(size, people, dim, strangers, TIGHT, seed)
    max_distance = 1 - fc.PICTO_CLUSTERING_SIMILARITY_THRESHOLD
    min_samples = fc.PICTO_CLUSTERING_MIN_SAMPLES

    base = _peak_mib()
    started = time.perf_counter()
    graph = _build_graph(mode, embeddings, max_distance)
    eps = _estimate_eps(mode, embeddings, min_samples)
    if eps is None:
        eps = fc.PICTO_CLUSTERING_EPS
    eps = max(min(eps, max_distance), 1e-6)
    labels = DBSCAN(
        eps=eps, min_samples=min_samples, metric="precomputed", n_jobs=-1
    ).fit_predict(graph)
    wall = time.perf_counter() - started

    return {
        "mode": mode,
        "size": int(len(labels)),
        "wall_s": round(wall, 2),
        "base_mib": None if base is None else round(base, 1),
        "peak_mib": None if _peak_mib() is None else round(_peak_mib(), 1),
        "edges": int(graph.nnz) if hasattr(graph, "nnz") else int(graph.size),
        "eps": round(eps, 6),
        "clusters": len({int(label) for label in labels if label != -1}),
        "noise": int((labels == -1).sum()),
        "ari": round(float(adjusted_rand_score(truth, labels)), 4),
    }


def _self_check() -> None:
    """Both graphs must partition identically at a shared eps.

    Isolates graph equivalence from the eps estimate, which is allowed to
    differ (the sparse path samples it).
    """
    embeddings, _ = _synthetic(600, 20, 128, 10, TIGHT, 0)
    max_distance = 1 - fc.PICTO_CLUSTERING_SIMILARITY_THRESHOLD
    min_samples = fc.PICTO_CLUSTERING_MIN_SAMPLES
    eps = 0.01

    dense = DBSCAN(
        eps=eps, min_samples=min_samples, metric="precomputed", n_jobs=-1
    ).fit_predict(_dense_graph(embeddings, max_distance))
    sparse = DBSCAN(
        eps=eps, min_samples=min_samples, metric="precomputed", n_jobs=-1
    ).fit_predict(_sparse_graph(embeddings, max_distance))

    assert _partition(dense) == _partition(
        sparse
    ), "sparse graph changed the clustering at a shared eps"
    print("self-check: sparse and dense graphs partition identically\n")


def _run_child(mode: str, size: int, args) -> dict:
    command = [
        sys.executable,
        os.path.abspath(__file__),
        "--child",
        "--mode",
        mode,
        "--size",
        str(size),
        "--people",
        str(args.people),
        "--dim",
        str(args.dim),
        "--strangers",
        str(args.strangers),
        "--seed",
        str(args.seed),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        # A child killed by the OOM reaper is the failure this script exists to show,
        # so report what it managed to say.
        raise SystemExit(
            f"{mode} n={size} benchmark child failed: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as e:
        raise SystemExit(f"{mode} n={size} benchmark child returned no valid JSON: {e}")


def _print_table(rows: list[dict]) -> None:
    header = (
        f"{'mode':<8}{'faces':>7}{'wall_s':>9}{'peak_MiB':>10}"
        f"{'delta_MiB':>11}{'edges':>12}{'clusters':>10}{'noise':>7}{'ARI':>8}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        peak = row["peak_mib"]
        base = row["base_mib"]
        delta = "" if peak is None or base is None else f"{peak - base:.1f}"
        print(
            f"{row['mode']:<8}{row['size']:>7}{row['wall_s']:>9.2f}"
            f"{'' if peak is None else format(peak, '.1f'):>10}{delta:>11}"
            f"{row['edges']:>12}{row['clusters']:>10}{row['noise']:>7}"
            f"{row['ari']:>8.4f}"
        )


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="1000,5000,10000")
    parser.add_argument("--modes", default="dense,sparse")
    parser.add_argument("--people", type=int, default=50)
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--strangers", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    # Child mode: one measurement, JSON on stdout.
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", default="sparse")
    parser.add_argument("--size", type=int, default=1000)
    return parser.parse_args()


def main() -> None:
    args = _parse()

    if args.child:
        print(
            json.dumps(
                _measure(
                    args.mode,
                    args.size,
                    args.people,
                    args.dim,
                    args.strangers,
                    args.seed,
                )
            )
        )
        return

    _self_check()

    sizes = [int(part) for part in args.sizes.split(",")]
    rows = [
        _run_child(mode, size, args) for mode in args.modes.split(",") for size in sizes
    ]
    _print_table(rows)


if __name__ == "__main__":
    main()
