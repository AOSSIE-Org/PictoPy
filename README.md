# PictoPy

PictoPy is an advanced desktop gallery application that combines the power of Tauri, React, and Rust for the frontend with a Python backend for sophisticated image analysis and management.

# Contributing

We welcome contributions of all kinds — code, documentation, tests, bug reports, and ideas. For full contribution guidelines, please read our [`CONTRIBUTING.md`](./CONTRIBUTING.md).

- **Chat & discuss:** Join our **[Discord Server](https://discord.gg/hjUhu33uAn)** (see Projects → PictoPy) to ask questions and propose changes.
- **Report issues:** Use GitHub Issues for bugs and feature requests.
- **Contribute code:** Fork the repo, create a descriptive branch (e.g., `feature/add-thing`), add tests and documentation, then open a Pull Request against `main`. Follow the coding standards and testing instructions in [`CONTRIBUTING.md`](./CONTRIBUTING.md).




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

- Smart tagging of photos based on detected objects, faces, and their recognition
- Traditional gallery features of album management
- Advanced image analysis with object detection and facial recognition
- Privacy-focused design with offline functionality
- Efficient data handling and parallel processing
- Smart search and retrieval
- Cross-platform compatibility

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

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the full license in [`LICENSE.md`](./LICENSE.md).