# PictoPy Features

### Gallery Application

- **Intelligent Photo Tagging**: Automatically tags photos based on detected objects, faces, and facial recognition.
- **Traditional Gallery Management**: Complete album organization and management tools.
- **Memories Feature**: Automatically organize photos into meaningful collections based on location and date, with Google Photos-style presentation.

### Advanced Image Analysis

- Object detection using **YOLOv11** for identifying various items in images
- Face detection and clustering powered by **FaceNet**.
- **Spatial Clustering**: Groups photos by location using DBSCAN algorithm (5km radius)
- **Temporal Grouping**: Organizes photos by date with monthly grouping
- **Reverse Geocoding**: Identifies actual city names from GPS coordinates

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
- Find visually or semantically similar images

### Memories Feature

Automatically creates meaningful photo collections inspired by Google Photos:

#### **On This Day**
- Shows photos from the same date in previous years
- Featured card display with "On this day last year" messaging
- Nostalgic look back at past moments

#### **Smart Grouping**
- **Location-based Memories**: Groups photos taken at the same location (5km radius using DBSCAN clustering)
  - Displays as "Trip to [City Name], [Year]" (e.g., "Trip to Jaipur, 2025")
  - Uses reverse geocoding to show actual city names
  - Supports 30+ major cities worldwide
- **Date-based Memories**: Groups photos by month for images without GPS data
  - Perfect for photos without location metadata
  - Organized chronologically

#### **Intelligent Filtering**
- Filter by All, Location, or Date memories
- View counts for each category
- Seamless navigation between memory types

#### **Memory Sections**
- **Recent Memories**: Last 30 days of captured moments
- **This Year**: All memories from the current year
- **All Memories**: Complete collection organized by recency

#### **Rich Viewing Experience**
- Full-screen image viewer with zoom support
- Slideshow mode for automatic playback
- Image metadata panel with EXIF data
- Keyboard shortcuts (Space, arrows, +/-, R, ESC)
- Thumbnail navigation strip
- Favorite marking and folder opening

#### **Technical Implementation**
- Backend: Python with DBSCAN clustering algorithm
- Frontend: React + Redux Toolkit for state management
- Real-time memory generation with configurable parameters
- Flexible clustering: works with date OR location (not both required)
- Efficient SQLite queries for fast retrieval

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
| API Framework     | FastAPI              |
| State Management  | Redux Toolkit        |
| Styling           | Tailwind CSS         |
| Routing           | React Router         |
| UI Components     | ShadCN               |
| Build Tool        | Vite                 |
| Type Checking     | TypeScript           |
