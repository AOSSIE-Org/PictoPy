# PictoPy

PictoPy is an advanced desktop gallery application that combines the power of Tauri, React, and Rust for the frontend with a Python backend for sophisticated image analysis and management.

## Architecture

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

- Smart tagging of photos based on detected objects, faces, and their recognition
- Traditional gallery features of album management
- Advanced image analysis with object detection and facial recognition
- Privacy-focused design with offline functionality
- Efficient data handling and parallel processing
- Smart search and retrieval
- Cross-platform compatibility

## Technical Stack

| Component | Technology |
| --------- | ---------- |
| Frontend | React |
| Desktop Framework | Tauri |
| Rust Backend | Rust |
| Python Backend | Python |
| Database | SQLite |
| Image Processing | OpenCV, ONNX Runtime |
| Object Detection | YOLOv8 |
| Face Recognition | FaceNet |
| API Framework | FastAPI |
| State Management | React Hooks |
| Styling | Tailwind CSS |
| Routing | React Router |
| UI Components | Radix UI |
| Build Tool | Vite |
| Type Checking | TypeScript |

## Setup

### Frontend Setup

#### Prerequisites
- Node.js (LTS version recommended)
- npm (comes with Node.js)
- Rust (latest stable version)
- Tauri CLI

#### Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

#### Running the Application
```bash
npm run tauri dev
```

#### Building for Production
```bash
npm run tauri build
```

### Python Backend Setup

#### Installation
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Set up a virtual environment (recommended)
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

#### Running the Backend
For UNIX-based systems:
```bash
./run.sh --test
```

The backend should now be running on port 8000 by default.

## Additional Resources
- [Tauri Documentation](https://tauri.app/v1/guides/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Troubleshooting
If you encounter any issues, please check the respective documentation for Tauri, React, and FastAPI. For persistent problems, feel free to open an issue in the project repository.
