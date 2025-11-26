# PictoPy

**PictoPy** is a powerful desktop photo gallery that fuses **Tauri, React,** and **Rust** with a **Python-based analysis backend** to deliver fast, private, and intelligent image management. <br>Designed for performance and offline use, PictoPy brings modern computer-vision capabilities to a cross-platform desktop experience.

### Quick Links

• [Documentation](https://aossie-org.github.io/PictoPy/)
• [Contributing Guide](./CONTRIBUTING.md) 
• [Screenshots](https://aossie-org.github.io/PictoPy/frontend/screenshots/)
• [Setup Instructions](./CONTRIBUTING.md)

# Architecture

### Frontend

- **Tauri**: Enables building the desktop application
- **React**: Used for creating the user interface
- **Rust**: Implements the high-performance backend logic and communicates with the frontend through Tauri APIs.
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
# Want to Contribute? 😄

&nbsp;&nbsp;&nbsp;<a href="https://discord.gg/hjUhu33uAn"><img src="https://github.com/user-attachments/assets/3ed93273-5055-4532-a524-87a337a4fbba" height="40"></a>

1. Join the **[Discord Server](https://discord.gg/hjUhu33uAn)** (Go to *Projects → PictoPy*) to interact with our community.  
2. For **detailed setup instructions, coding guidelines, and the contribution process**, please check out our **[contributing guidelines](./CONTRIBUTING.md)**.    


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
## Need Help?
Join our [Discord](https://discord.gg/hjUhu33uAn) for guidance on the project.

---

## Our Code of Conduct:

 [CODE OF CONDUCT](./CODE_OF_CONDUCT.md)
