# Database

## Overview

PictoPy uses several SQLite databases to manage various aspects of the application. This document provides an overview of each database, its structure, and its primary operations.

## Database Schema

<!-- markdownlint-disable MD033 -->
<iframe width="560" height="315" src='https://dbdiagram.io/e/6a593dd1c3a90dd98d55554d/6a5b4a02067336e1dea2347a'> </iframe>
<!-- markdownlint-enable MD033 -->

Alternatively, [click here to view the interactive DB schema diagram in a new tab](https://dbdiagram.io/d/PictoPy-6a593dd1c3a90dd98d55554d).

!!! note "Diagram"
    The embedded ER diagram above does not yet include the four Smart Memories tables (`memories`, `memory_images`, `memory_videos`, `memory_runs`). Use the [Memories tables](#memories-tables) section below for those.

## Memories tables

Defined and created by `db_create_memories_table()` in
`backend/app/database/memories.py`, which also holds every query helper the
Smart Memories feature uses. See [Memories](memories.md) for the feature
itself.

The module connects through `_connect` imported from
`app/database/images.py`, which issues `PRAGMA foreign_keys = ON` on every
connection, so the `ON DELETE CASCADE` and `ON DELETE SET NULL` rules below
are actually enforced.

### `memories`

One row per curated memory.

| Column             | Type     | Notes                                                          |
| ------------------ | -------- | -------------------------------------------------------------- |
| `memory_id`        | TEXT     | Primary key                                                    |
| `dedupe_key`       | TEXT     | NOT NULL, UNIQUE. Upserts conflict-resolve on this column      |
| `event_type`       | TEXT     | NOT NULL, CHECK against `EVENT_TYPES`                          |
| `status`           | TEXT     | NOT NULL, DEFAULT `'pending'`, CHECK against `MEMORY_STATUSES` |
| `title`            | TEXT     | NOT NULL                                                       |
| `subtitle`         | TEXT     | Nullable                                                       |
| `place_label`      | TEXT     | Nullable                                                       |
| `center_lat`       | REAL     | Nullable                                                       |
| `center_lon`       | REAL     | Nullable                                                       |
| `surface_date`     | DATE     | NOT NULL. The date the memory is eligible to appear            |
| `period_start`     | DATETIME | Earliest capture time of the member images                     |
| `period_end`       | DATETIME | Latest capture time of the member images                       |
| `cover_image_id`   | TEXT     | FK → `images(id)` ON DELETE SET NULL                           |
| `image_count`      | INTEGER  | NOT NULL, DEFAULT 0                                            |
| `video_count`      | INTEGER  | NOT NULL, DEFAULT 0                                            |
| `score`            | REAL     | NOT NULL, DEFAULT 0                                            |
| `signals`          | TEXT     | JSON blob, decoded on read                                     |
| `params_signature` | TEXT     | Identifies the scorer configuration that built the row         |
| `error`            | TEXT     | Nullable                                                       |
| `notified_at`      | DATETIME | Nullable                                                       |
| `viewed_at`        | DATETIME | Nullable                                                       |
| `dismissed`        | BOOLEAN  | NOT NULL, DEFAULT 0                                            |
| `created_at`       | DATETIME | DEFAULT `CURRENT_TIMESTAMP`                                    |
| `updated_at`       | DATETIME | DEFAULT `CURRENT_TIMESTAMP`                                    |

`db_upsert_memory()` writes every column except `memory_id`, `viewed_at`,
`notified_at` and `dismissed`, so re-curating a memory replaces its contents
without resetting what the user has already seen.

### `memory_images`

Join table between a memory and its curated photos.

| Column       | Type    | Notes                                                  |
| ------------ | ------- | ------------------------------------------------------ |
| `memory_id`  | TEXT    | NOT NULL. FK → `memories(memory_id)` ON DELETE CASCADE |
| `image_id`   | TEXT    | NOT NULL. FK → `images(id)` ON DELETE CASCADE          |
| `sort_order` | INTEGER | NOT NULL. Presentation order                           |
| `score`      | REAL    | Nullable. Per-image score within this memory           |

Primary key is the composite `(memory_id, image_id)`. Rows cascade away from
both parents: deleting a memory drops its members, and deleting a photo from
the library removes it from every memory holding it.

### `memory_videos`

The same shape for short video clips.

| Column       | Type    | Notes                                                  |
| ------------ | ------- | ------------------------------------------------------ |
| `memory_id`  | TEXT    | NOT NULL. FK → `memories(memory_id)` ON DELETE CASCADE |
| `video_id`   | TEXT    | NOT NULL. FK → `videos(id)` ON DELETE CASCADE          |
| `sort_order` | INTEGER | NOT NULL                                               |
| `score`      | REAL    | Nullable                                               |

Primary key is `(memory_id, video_id)`. `sort_order` is a single sequence
shared with `memory_images`, so merging the two tables by `sort_order`
produces one chronological story.

### `memory_runs`

One row per curation run, keyed by date. A run that generates zero memories
is a legitimate outcome, so the `memories` table alone cannot answer "has
today's run already happened?".

| Column             | Type     | Notes                                      |
| ------------------ | -------- | ------------------------------------------ |
| `run_date`         | DATE     | Primary key                                |
| `status`           | TEXT     | NOT NULL, CHECK against `RUN_STATUSES`     |
| `params_signature` | TEXT     | Nullable                                   |
| `generated_count`  | INTEGER  | NOT NULL, DEFAULT 0                        |
| `error`            | TEXT     | Nullable                                   |
| `started_at`       | DATETIME | DEFAULT `CURRENT_TIMESTAMP`                |
| `finished_at`      | DATETIME | Set when the run reaches a terminal status |

### Constrained vocabularies

Three module-level constants in `app/database/memories.py` define the allowed
values, and the `CHECK` clauses in the DDL are generated from those same
tuples by the `_check_in()` helper, so constants and constraints cannot drift
apart.

| Constant          | Column                | Values                                          |
| ----------------- | --------------------- | ----------------------------------------------- |
| `EVENT_TYPES`     | `memories.event_type` | `anniversary`, `import_event`, `semantic_event` |
| `MEMORY_STATUSES` | `memories.status`     | `pending`, `complete`, `failed`, `empty`        |
| `RUN_STATUSES`    | `memory_runs.status`  | `running`, `complete`, `failed`                 |

`db_finish_memory_run()` additionally rejects any terminal status other than
`complete` or `failed`.

### Indexes

| Index                        | Table                                     | Serves                                                                                 |
| ---------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------- |
| `ix_memories_surface_date`   | `memories(surface_date DESC)`             | Newest-first listing                                                                   |
| `ix_memories_status_surface` | `memories(status, surface_date DESC)`     | The filtered, paginated card list                                                      |
| `ix_memories_surfaceable`    | `memories(surface_date DESC, score DESC)` | Partial index (see below) — the "is there anything to show?" lookup                    |
| `ix_memory_images_image_id`  | `memory_images(image_id)`                 | Reverse lookup by photo; without it SQLite scans `memory_images` on every image delete |
| `ix_memory_videos_video_id`  | `memory_videos(video_id)`                 | The same reverse lookup for clips                                                      |

`ix_memories_surfaceable` is a partial index, covering only the rows a
surface check can possibly return:

```sql
CREATE INDEX IF NOT EXISTS ix_memories_surfaceable
ON memories(surface_date DESC, score DESC)
WHERE viewed_at IS NULL AND dismissed = 0 AND status = 'complete'
```

### Table creation order

`memory_images` references `images(id)` and `memory_videos` references
`videos(id)`, so both parent tables must exist first. In `main.py`'s
`lifespan()` the calls run in this order:

1. `db_create_images_table()`
2. `db_create_videos_table()`
3. …other tables…
4. `db_create_memories_table()`

`db_create_videos_table()` must run before `db_create_memories_table()`. The
test fixtures in `backend/tests/conftest.py` create the tables in the same
order.

`memories.video_count` is also added by a guarded `ALTER TABLE`: the module
reads `PRAGMA table_info(memories)` and appends the column only when it is
missing, because `CREATE TABLE IF NOT EXISTS` will not add a column to a
table that a pre-existing database already has.

### Memories capture dates

`images.captured_at` (and `videos.captured_at`) is a distinct column from the
`date_created` value stored inside the `metadata` JSON blob. `date_created`
drives gallery display; `captured_at` is consumed only by memories. The
candidate queries that gather media for a run filter on
`captured_at IS NOT NULL`, so media without a trusted capture date is never
curated. Reads of already-generated memories go through the `memories` table
instead, which has no `captured_at` of its own and is queried on fields such
as `surface_date` and `status`.

`metadata` also carries `date_source`, recording where the date came from:
`exif`, `sidecar`, `container`, `filesystem` or `unknown`. Only the first
three are treated as trusted capture times (`TRUSTED_DATE_SOURCES` in
`app/utils/extract_location_metadata.py`); a filesystem mtime is import day
for a copied library, so it never reaches `captured_at`, which is left `NULL`
and therefore invisible to memories.

Both `images` and `videos` carry an index on `captured_at`
(`ix_images_captured_at`, `ix_videos_captured_at`), and `images` additionally
has `ix_images_favourite_captured_at` on `(isFavourite, captured_at)`.
