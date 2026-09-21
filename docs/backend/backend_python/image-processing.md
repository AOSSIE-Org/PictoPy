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
128-dimensional embedding array for each detected face in the image, normalised to unit length so that comparing two
faces is a single dot product.

Not every detected face is worth embedding. A face must pass a quality gate first: it needs to be at least
`PICTO_CLUSTERING_MIN_FACE_SIZE` (1000 px²) and not too blurry. Below that size FaceNet's embeddings stop telling
people apart, and unrelated faces start to look like the same person.

## Face Clustering

Now, here's where it gets interesting:

We use something called DBSCAN to group similar faces together. A full recluster runs when the last one is more than
24 hours old, or when more than 100 faces are waiting for a cluster. In between, each new face is assigned to the
cluster whose mean embedding it is most similar to, provided the similarity is at least 0.8.

## Finding People in Videos

Videos can show up under the people in them too. This is **off by default**, because it runs a second detector over
every keyframe with a person in it; turn it on under **Settings → Video Tagging → Find People in Videos**.

Videos are never analysed frame by frame. Instead, PictoPy samples keyframes (one every few seconds, set by the
keyframe interval) and stores them as JPEGs up to 1280 px on the long side. That size matters: at 640 px most faces in
a video are too small to pass the quality gate above.

For each video:

1. YOLOv11 looks at every keyframe. Only keyframes where it sees a `person` go on to face detection.
2. Faces are detected, quality-gated and embedded exactly as they are for photos.
3. Near-identical faces are dropped (the same person in a neighbouring keyframe), keeping the most confident one, and
   each video keeps at most 40 faces, so a crowd scene can't flood the database.

???+ warning "Video faces join people; they never create them"
Faces from videos are **never** fed to DBSCAN. Keyframes include motion blur, odd angles and partial faces, and these
act as bridges: DBSCAN can chain through them and merge several different people into one cluster.

Instead, each video face is attached to the nearest existing person, found from photos, when its similarity to that
person's mean is at least 0.65 (`PICTO_CLUSTERING_SIMILARITY_THRESHOLD`). A face that matches no one is kept but left
unassigned. Only photo faces count towards a person's mean, and one keyframe can attach to the same person only once.

A person's card counts **photos only** ("12 photos · 3 videos"), and the photo count alone decides how people are
ordered.

### Scanning videos that were already tagged

Videos tagged before the setting was turned on have no faces yet. **Settings → Video Tagging → Scan videos** finds
them in the background and shows its progress; the same scan also runs as part of any later folder sync or AI
tagging pass.

The scan does not re-tag these videos. It keeps each keyframe, its timestamp and its semantic search embedding, and
only re-samples a keyframe at full resolution if it shows a person and was stored smaller than the source allows. Each
video is marked once it has been scanned (`videos.facesScanned`), so an interrupted scan picks up where it stopped.

### Where video faces appear

- **A person's page** lists their videos alongside their photos.
- **Searching for several people** returns videos too, matching any or all of them.
- **Searching by a photo or the webcam** returns videos, ranked by their best-matching keyframe.

Videos always play from the start; jumping to the moment a person appears is not supported yet.

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

## How It All Fits Together

When you add a new photo, we first look for objects and faces. If we find faces, we generate embeddings for them. These embeddings then get added to our face clusters.
Then, if the semantic search models are installed, we generate a SigLIP2 embedding for the photo too.
Videos follow once the photos are done: their keyframes are tagged, and, if finding people in videos is on, their
faces are attached to the people found in your photos.
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
| `conf_thres` | 0.45                           | Confidence threshold for face detection |
| `iou_thres`  | 0.45                           | IoU threshold for NMS in face detection |
| Model Path   | `DEFAULT_FACE_DETECTION_MODEL` | Path to the face detection model file   |

### FaceNet (Face Recognition)

| Parameter   | Value                   | Description                          |
| ----------- | ----------------------- | ------------------------------------ |
| Model Path  | `DEFAULT_FACENET_MODEL` | Path to the FaceNet model file       |
| Input Shape | (1, 3, 160, 160)        | Expected input shape for face images |
| Output      | 128-dimensional vector  | Face embedding, unit length          |

### Face Clustering (DBSCAN)

| Parameter | Value | Description |
| --------- | ----- | ----------- |
| `eps` | Adaptive | Estimated from the data, capped at 0.35 (1 − the 0.65 similarity threshold). 0.75 (`PICTO_CLUSTERING_EPS`) is used only when there are too few faces to estimate it |
| `min_samples` | 2 | Number of samples in a neighborhood for a point to be considered as a core point. Values below 2 are reset to 2 to prevent chaining |
| `metric` | "cosine" | Distance metric used for clustering |

### Faces in Videos

| Parameter | Value | Description |
| --------- | ----- | ----------- |
| `Video_Face_Detection` | Off | User preference (Settings → Video Tagging). `VIDEO_FACE_DETECTION` sets the default |
| `VIDEO_FRAME_MAX_DIMENSION` | 1280 | Longest side of a stored keyframe. Smaller frames leave most video faces below the quality gate |
| `PICTO_CLUSTERING_MIN_FACE_SIZE` | 1000 px² | Smallest face that is embedded, for photos and videos alike |
| `VIDEO_FACE_DEDUPE_THRESHOLD` | 0.92 | Cosine similarity above which two faces in one video count as the same appearance |
| `VIDEO_MAX_FACES_PER_VIDEO` | 40 | Most faces kept per video, highest confidence first |
| `PICTO_CLUSTERING_SIMILARITY_THRESHOLD` | 0.65 | Minimum similarity to a person's photo mean for a video face to attach to them |

### Semantic Search (SigLIP2)

| Parameter | Value | Description |
| -------------------------- | ---------------------------------- | ---------------------------------------------------------------------------- |
| Default checkpoint | `base` | Set via `SIGLIP2_ACTIVE_CHECKPOINT`; `large` and `so400m` also exist but ship placeholder registry entries only (see [Semantic Search](semantic-search.md#model-distribution-and-checkpoints)). |
| Input resolution (`base`) | 224 × 224 | Larger checkpoints use 384 × 384. |
| Embedding dimension | 768 | Same dimensionality for both the image and text towers. |
| `SIGLIP2_EMBED_BATCH_SIZE` | 8 | Images per batch during the background embedding pass. |
| `SIGLIP2_MATCH_THRESHOLD` | 0.01 | Minimum sigmoid score to count as a match. SigLIP2's absolute scores run low even for real matches — this is expected, not a bug. |
| Output | Sorted, scored image list | Scores are rounded to 4 decimal places server-side and never shown in the UI. |

Note: Some of these values are default parameters and can be adjusted when initializing the models or during runtime, depending on the specific use case or performance requirements.
