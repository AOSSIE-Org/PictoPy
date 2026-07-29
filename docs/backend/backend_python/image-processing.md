# Image Processing

We use Python’s Process Pool Executor for parallel image processing in background worker processes. This allows multiple images to be processed in parallel without blocking the API or frontend.

PictoPy uses different models for achieving its tagging capabilities.
The discussed models below are default models, you can change them by going to `app/models` directory and change the paths in the configuration files.

## Object Detection with YOLOv11

We use YOLOv11 to spot objects in your photos. Here's what it does:

YOLOv11 takes your image and runs it through its model. It figures out what objects are in the image and where they are.
The result is a list of objects, their locations, and how confident the model is about each detection. If a `person` class is predicted we pass it on
to the face detection model which we discuss in the next section.

???+ tip "Fun Fact"
YOLO stands for "You Only Look Once". We use the model provided by [Ultralytics](https://github.com/ultralytics/ultralytics) by default.

## Face Detection and Recognition

For faces, we do a bit more:

We start with a special version of YOLOv11 that's really good at finding faces. Once we find a face, we zoom in on it
(by cropping it to `160x160` - the shape FaceNet expects) and pass it to our FaceNet model.
FaceNet then creates a unique 'embedding' for each face, the representation of the face in a form of numbers.

???+ tip "Fun Fact"
We use another YOLOv11 model for this as well by default. This was pretrained on top of the one provided by Ultralytics and is called
[yolov11-face](https://github.com/akanametov/yolo-face)

???+ note "What's an embedding?"
An embedding is a bunch of numbers that represent the face. Similar faces will have similar numbers. FaceNet creates a
512-dimensional embedding array for each detected face in the image.

## Face Clustering

Now, here's where it gets interesting:

We use something called DBSCAN to group similar faces together. This process happens automatically as you add new photos to the system, we perform reclustering
after every 5 photos are added (this can be changed in the code) but apart from that, the photos are assigned a cluster based on the embedding distance
of the faces in the photo with the mean of each of the clusters.

## Semantic Search with SigLIP2

Beyond tag-based search (finding photos by the exact object/face labels YOLO
and FaceNet detected), PictoPy can also search photos by **describing** them
in plain language — "beach sunset", "two people hugging" — using Google's
[SigLIP2](https://huggingface.co/docs/transformers/en/model_doc/siglip2)
model.

Every photo gets a single numeric "embedding" computed once, in the
background, right after the usual object/face tagging pass finishes. When
you search, your query gets embedded the same way and compared against every
stored photo embedding — so a phrase the app has never seen before still
works immediately, with no re-scan of your library required.

Just type into the same search box you already use. There's no separate
"semantic search" mode to switch on: PictoPy tries an exact tag match first,
and only falls back to meaning-based search if that comes up empty (and the
feature is installed).

???+ tip "Fun Fact"
SigLIP2 stands for "Sigmoid Loss for Language-Image Pre-training, v2". Unlike
its predecessor CLIP, it uses a per-pair sigmoid loss instead of a
whole-batch softmax during training — this is why its match scores look
different from what you might expect (see the parameters table below).

???+ note "Installing it"
Semantic search is an optional ~1.5 GB download from **Settings → AI
Models**, listed as a "Semantic Search" bundle (three files: a vision model,
a text model, and a tokenizer). If it isn't installed, tag search keeps
working exactly as before — semantic search just silently doesn't
contribute any results.

For the full technical breakdown — architecture diagrams, database schema,
model calibration details, and known limitations — see the dedicated
[Semantic Search](semantic-search.md) page.

## Capture Dates and Location

Indexing records two different dates per file, and they are not
interchangeable.

| Where it lives                                    | What it holds                                                                             | Who reads it                           |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------- |
| `date_created`, inside the `metadata` JSON column | The best date available, always populated — it falls back to the file's modification time | Gallery display and sorting            |
| `captured_at`, a column on `images` and `videos`  | When the shutter actually fired; `NULL` when nothing trustworthy was found                | The Memories feature, and nothing else |

The same `metadata` JSON carries a `date_source` field saying where the date
came from:

| `date_source` | Meaning                                          | Trusted |
| ------------- | ------------------------------------------------ | ------- |
| `exif`        | Read from the image's own EXIF tags              | Yes     |
| `sidecar`     | Read from a Google Takeout sidecar JSON file     | Yes     |
| `container`   | Read from an MP4/MOV container box               | Yes     |
| `filesystem`  | The file's mtime, standing in for a capture date | No      |
| `unknown`     | The file could not be opened or stat'd at all    | No      |

The trusted set is `TRUSTED_DATE_SOURCES` in
`app/utils/extract_location_metadata.py`. `MetadataExtractor.extract_datetime()`
returns `None` when `date_source` is anything outside it, and
`video_util_prepare_video_records()` applies the same test, so an untrusted
date is written to `captured_at` as `NULL` while `date_created` keeps it for
the UI.

### EXIF

`DateTimeOriginal` is not in IFD0 — it sits behind the EXIF sub-IFD pointer
`0x8769`, and Pillow's `getexif()` returns IFD0 only. `_extract_capture_datetime()`
searches both: for each of `DateTimeOriginal`, `DateTimeDigitized` and
`DateTime`, in that order, it reads the sub-IFD first and then IFD0. If nothing
parses, `date_created` falls back to the file mtime and `date_source` becomes
`filesystem`.

GPS comes off the same EXIF object via `_extract_gps_coordinates()`, which
reads the GPSInfo IFD and converts degrees/minutes/seconds to signed decimal
degrees.

### Google Takeout sidecars

A Google Photos export strips EXIF from part of its own library and parks the
real values in a sibling JSON file. When EXIF yields no date or no coordinates,
`takeout_sidecar_read()` (`app/utils/takeout_sidecar.py`) looks for that file.

| Sidecar spelling                       | How it is found                        |
| -------------------------------------- | -------------------------------------- |
| `<file>.supplemental-metadata.json`    | Probed by exact name                   |
| `<file>.json`                          | Probed by exact name                   |
| `<file>.supplemental-metadata(1).json` | Found by prefix in a directory listing |

The exact spellings cost one `stat` each and are tried first; the directory is
only listed if neither produced a usable sidecar, and that listing is cached —
one entry, keyed on the directory path and its mtime — so a folder of N photos
does not cost N scans.

Once a sidecar is open:

- `photoTakenTime` is preferred over `creationTime`, which is the upload time.
- Coordinates come from `geoData`, falling back to `geoDataExif`.
- Takeout writes `0/0` rather than null for "no location", so an exact
  (0.0, 0.0) pair is discarded.
- Album-level metadata files match no image and are skipped by key: a payload
  containing `entries` or `albumData` is rejected.

The datetime is returned in EXIF format (`%Y:%m:%d %H:%M:%S`) so callers parse
it exactly as they parse a real EXIF value.

### Videos

Video capture dates are parsed straight out of the ISO base media container
boxes by `app/utils/video_capture_date.py`. There is no ffmpeg or ffprobe
dependency — PictoPy ships through PyInstaller and cannot assume either exists
on the machine. OpenCV, which handles the poster frame, exposes no creation
date at all.

`_resolve_capture_date()` in `app/utils/videos.py` takes the first source that
answers:

| Order | Source                                                          | `date_source` | Notes                                                                          |
| ----- | --------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------ |
| 1     | `com.apple.quicktime.creationdate` in `moov/meta` (keys + ilst) | `container`   | Carries its own UTC offset, so it yields the wall-clock time of the shot       |
| 2     | Google Takeout sidecar                                          | `sidecar`     | Same reader as photos                                                          |
| 3     | `moov/mvhd` creation time                                       | `container`   | UTC seconds since 1904-01-01, converted to local time; a re-encode rewrites it |
| 4     | File mtime                                                      | `filesystem`  | Untrusted, so it never reaches `captured_at`                                   |

Values outside 1990-01-01 through two days from now are treated as noise — a
container can carry 0, or a clock that was never set — and a malformed keys
table is bounded at `MAX_METADATA_KEYS = 512` entries.

The filesystem mtime is recorded in its own field, `metadata["file_modified"]`.
`video_util_source_is_unchanged()` compares a video's size and that stored mtime
to decide whether to re-index it; a row without `file_modified` is treated as
changed, so its container is read once and its date corrected.

For what consumes `captured_at`, see the [Memories](memories.md) page.

## How It All Fits Together

When you add a new photo, we first look for objects and faces. If we find faces, we generate embeddings for them. These embeddings then get added to our face clusters.
Then, if the semantic search models are installed, we generate a SigLIP2 embedding for the photo too.
All this information gets stored in our database so we can find it later.

## Under the Hood

We're using ONNX runtime to run our AI models quickly. Everything's stored in SQLite databases, making it easy to manage.
The system updates clusters as you add or remove photos, so it keeps getting smarter over time.

## PictoPy Model Parameters

Here are some key parameters for the main models used in PictoPy's image processing pipeline.

### YOLOv11 Object Detection

| Parameter    | Value    | Description                                     |
| ------------ | -------- | ----------------------------------------------- |
| `conf_thres` | 0.4      | Confidence threshold for object detection       |
| `iou_thres`  | 0.5      | IoU (Intersection over Union) threshold for NMS |
| Input Shape  | Varies   | Determined dynamically from the model           |
| Output       | Multiple | Includes bounding boxes, scores, and class IDs  |

### Face Detection (YOLOv11 variant)

| Parameter    | Value                          | Description                             |
| ------------ | ------------------------------ | --------------------------------------- |
| `conf_thres` | 0.35                           | Confidence threshold for face detection |
| `iou_thres`  | 0.45                           | IoU threshold for NMS in face detection |
| Model Path   | `DEFAULT_FACE_DETECTION_MODEL` | Path to the face detection model file   |

### FaceNet (Face Recognition)

| Parameter   | Value                   | Description                          |
| ----------- | ----------------------- | ------------------------------------ |
| Model Path  | `DEFAULT_FACENET_MODEL` | Path to the FaceNet model file       |
| Input Shape | (1, 3, 160, 160)        | Expected input shape for face images |
| Output      | 512-dimensional vector  | Face embedding dimension             |

### Face Clustering (DBSCAN)

| Parameter     | Value    | Description                                                                                |
| ------------- | -------- | ------------------------------------------------------------------------------------------ |
| `eps`         | 0.3      | Maximum distance between two samples for them to be considered as in the same neighborhood |
| `min_samples` | 2        | Number of samples in a neighborhood for a point to be considered as a core point           |
| `metric`      | "cosine" | Distance metric used for clustering                                                        |

### Semantic Search (SigLIP2)

| Parameter                  | Value                     | Description                                                                                                                                                                                     |
| -------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Default checkpoint         | `base`                    | Set via `SIGLIP2_ACTIVE_CHECKPOINT`; `large` and `so400m` also exist but ship placeholder registry entries only (see [Semantic Search](semantic-search.md#model-distribution-and-checkpoints)). |
| Input resolution (`base`)  | 224 × 224                 | Larger checkpoints use 384 × 384.                                                                                                                                                               |
| Embedding dimension        | 768                       | Same dimensionality for both the image and text towers.                                                                                                                                         |
| `SIGLIP2_EMBED_BATCH_SIZE` | 8                         | Images per batch during the background embedding pass.                                                                                                                                          |
| `SIGLIP2_MATCH_THRESHOLD`  | 0.01                      | Minimum sigmoid score to count as a match. SigLIP2's absolute scores run low even for real matches — this is expected, not a bug.                                                               |
| Output                     | Sorted, scored image list | Scores are rounded to 4 decimal places server-side and never shown in the UI.                                                                                                                   |

Note: Some of these values are default parameters and can be adjusted when initializing the models or during runtime, depending on the specific use case or performance requirements.
