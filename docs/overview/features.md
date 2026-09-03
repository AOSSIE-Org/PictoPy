# PictoPy Features

## Gallery Application

- **Intelligent Photo Tagging**: Automatically tags photos based on detected objects, faces, and facial recognition.
- **Traditional Gallery Management**: Complete album organization and management tools.
- **Memories Feature**: Automatically curates photos and short clips into collections that resurface on their own, played back as full-screen stories.

### Advanced Image Analysis

- Object detection using **YOLOv11** for identifying various items in images
- Face detection and clustering powered by **FaceNet**, with DBSCAN grouping face embeddings into people you can name
- **Scene and event recognition**: **SigLIP2** labels photos with the scene and the kind of occasion they show — weddings, festivals, hikes, birthdays and similar
- **Capture dates**: reads the date a shot was actually taken from EXIF, Google Takeout sidecar files, or the video container itself, so a copied library still groups by when the photos were taken

### Privacy-Focused Design

- **Entirely offline**: All data stays on your local machine.
- No reliance on remote servers for processing.
- Models are stored locally and customizable by the user.

### Efficient Data Handling & Processing

- Lightweight **SQLite** database for storing image metadata, face embeddings, and album info.
- Background image processing using `asyncio` for a smooth UI experience.

### Smart Search & Retrieval

- Search photos based on:
  - Detected objects
  - Recognized faces
  - Embedded metadata
- **Semantic Search** (optional, ~1.5 GB download): describe a photo in your
  own words — "beach sunset", "two people hugging" — and find it even if no
  detected tag matches the exact phrase. Powered by
  [SigLIP2](https://huggingface.co/docs/transformers/en/model_doc/siglip2),
  running fully on-device via ONNX Runtime. Falls back automatically from
  tag search; no mode switch required.

### Memories Feature

Curates photos and short video clips into stories worth looking back on, and
brings them to you instead of waiting to be browsed. See
[Memories](../frontend/memories.md) for the full walkthrough.

#### **How Memories Reach You**

- Memories are curated in the background while your library is indexed, so they
  are already waiting the next time you open the app
- The Memories page shows how many new memories you have not looked at yet
- A **Refresh** button curates on demand, and tells you to wait if indexing is
  still running rather than scoring a half-processed library

#### **Kinds of Memories**

- **Anniversaries**: photos taken on this date in previous years
- **Import events**: a burst of photos from a single outing, separated from the
  rest of your library wherever there is a long gap in time or a big jump in
  distance
- **Recognized occasions**: photos that on-device **SigLIP2** recognizes as one
  event — weddings, festivals, hikes, birthdays and similar

#### **Choosing the Photos**

- Every candidate photo is ranked, so the best ones lead the story
- Ranking favors your favorites, photos of people you have named, recognized
  occasions, photos with faces in them, and places away from home
- Near-duplicates are dropped, so a burst of near-identical frames does not fill
  a memory with the same shot
- Photos that do not visually belong with the rest of an outing are trimmed out
- The survivors are spread across the memory's time span rather than clumped at
  one end
- Short video clips shot during the same span are woven in alongside the photos
  in chronological order; the cover is always a still

#### **Story Viewer**

- Full-screen, Instagram-style playback with a segmented progress bar, one
  segment per slide
- Autoplays and advances on its own; a clip is held for its own length instead
  of a fixed interval
- Keyboard navigation (arrow keys, Space to pause or resume, Esc to close) and
  swipe navigation
- Clips play silently, with a per-slide sound toggle
- A filmstrip along the bottom jumps straight into another memory
- Opening a memory clears its unread state

#### **Titles**

- A memory is named after what its photos are actually of, using the occasion or
  scene that best describes the ones that made the final cut
- When nothing is recognized confidently enough, a generic title is used and the
  date moves to the subtitle

#### **Settings**

- Turn memory generation off entirely
- Set the smallest and largest number of photos a memory may hold
- Set how long each photo is held before the story advances
- Adjust the relative weight of each ranking signal through user preferences

#### **Technical Implementation**

- Backend: Python, curating on a background worker so a curation failure never
  interrupts or fails an import
- Frontend: React, with React Query for server state and Redux Toolkit for
  viewer state
- Curated memories are stored in SQLite and read back by the UI, so a story
  opens immediately rather than being recomputed on view
- Deleting a memory removes only the collection; the photos stay in your library

### Cross-Platform Compatibility

- Available on major operating systems (Windows, macOS, Linux)

## Technical Stack

| Component         | Technology           |
| ----------------- | -------------------- |
| Frontend          | React                |
| Desktop Framework | Tauri                |
| Rust Backend      | Rust                 |
| Python Backend    | Python               |
| Database          | SQLite               |
| Image Processing  | OpenCV, ONNX Runtime |
| Object Detection  | YOLOv11              |
| Face Recognition  | FaceNet              |
| Semantic Search   | SigLIP2              |
| API Framework     | FastAPI              |
| State Management  | Redux Toolkit        |
| Styling           | Tailwind CSS         |
| Routing           | React Router         |
| UI Components     | ShadCN               |
| Build Tool        | Vite                 |
| Type Checking     | TypeScript           |
