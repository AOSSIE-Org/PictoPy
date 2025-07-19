# PictoPy Features

### Gallery Application

- **Intelligent Photo Tagging**: Automatically tags photos based on detected objects, faces, and facial recognition.
- **Traditional Gallery Management**: Complete album organization and management tools.

### Advanced Image Analysis

- Object detection using **YOLOv8** for identifying various items in images
- Face detection and clustering powered by **FaceNet**.

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
| Object Detection  | YOLOv8               |
| Face Recognition  | FaceNet              |
| API Framework     | FastAPI              |
| State Management  | Redux Toolkit        |
| Styling           | Tailwind CSS         |
| Routing           | React Router         |
| UI Components     | ShadCN               |
| Build Tool        | Vite                 |
| Type Checking     | TypeScript           |
