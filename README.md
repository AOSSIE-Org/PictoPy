# PictoPy

PictoPy is an advanced desktop gallery application that combines the power of Tauri, React, and Rust for the frontend with a Python backend for sophisticated image analysis and management.

# Want to Contribute? 😄

&nbsp;&nbsp;&nbsp;<a href="https://discord.gg/hjUhu33uAn"><img src="https://github.com/user-attachments/assets/3ed93273-5055-4532-a524-87a337a4fbba" height="40"></a>

1. First, join the **[Discord Server](https://discord.gg/hjUhu33uAn) (Go to Projects->PictoPy)** to chat with everyone.
2. For detailed setup instructions, coding guidelines, and the contribution process, please check out our [CONTRIBUTING.md](./CONTRIBUTING.md) file.

# Architecture

### Frontend

- **Tauri**: Enables building the desktop application
- **React**: Used for creating the user interface
- **Rust**: Powers the backend, which the frontend communicates with through Tauri's API

### Backend (Python)

- **FastAPI**: Serves as the API framework
- **SQLite**: Database for storing metadata and embeddings
- **YOLO**: Used for object detection
- **FaceNet**: Generates face embeddings
- **ONNX Runtime**: Runs the models efficiently
- **DBSCAN**: Performs clustering for face embeddings

### Backend (Rust via Tauri)

Handles file system operations and provides a secure bridge between the frontend and local system.

## Features

- **Smart Tagging**: Automatic photo tagging based on detected objects, faces, and their recognition
- **Batch Operations**: Select multiple images and perform bulk actions (delete, tag, move to album, export)
- **Album Management**: Traditional gallery features for organizing your photos
- **Advanced Image Analysis**: Object detection and facial recognition powered by AI
- **Privacy-Focused**: Offline functionality with all processing done locally
- **Efficient Processing**: Parallel processing for handling large photo collections
- **Smart Search**: Quick retrieval with advanced search capabilities
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Keyboard Shortcuts**: Ctrl+A to toggle select/deselect all, Escape to deselect (works on all platforms including Mac)

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

---

Our Code of Conduct: [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
