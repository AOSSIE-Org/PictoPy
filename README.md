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
## Installation Guide

PictoPy installation guide (as of December 13, 2025)


PictoPy is a *privacy-first desktop image gallery application* developed by AOSSIE. It features object detection, face clustering, and image sorting using a Python backend for analysis, combined with a frontend built using *Tauri* (Rust + React).

It's cross-platform (Windows, macOS, Linux) but requires building from source, as pre-built releases may not be available yet.

### Prerequisites
- *Git* (to clone the repository)
- *Node.js* and *npm/yarn/pnpm* (for the frontend)
- *Rust* (via [rustup](https://rustup.rs/))
- *Python 3.10+* (for the backend)
- *Tauri dependencies* (platform-specific system libraries)

### Step-by-Step Installation

1. *Clone the Repository*
   
   git clone https://github.com/AOSSIE-Org/PictoPy.git
   cd PictoPy
   

2. *Install Frontend Dependencies*
   Navigate to the frontend directory (usually src-tauri or root has package.json):
   
   npm install   # or yarn install / pnpm install
   

3. *Install Python Backend Dependencies*
   The project includes a requirements.txt file listing all needed packages (e.g., OpenCV, face_recognition, torch, etc.).
   
   python -m venv venv          # Optional: create a virtual environment
   source venv/bin/activate     # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   

   *Note on System Dependencies*:
   Some Python packages (especially OpenCV) require system libraries:
   - *Ubuntu/Debian*:
     
     sudo apt update
     sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6
     
   - *Fedora*:
     
     sudo dnf install mesa-libGL
     
   - *macOS* (using Homebrew):
     
     brew install libgl1
     
   - *Windows*: Usually handled automatically by pip wheels, but ensure Visual C++ Build Tools are installed.

4. *Install Tauri CLI*
   
   cargo install tauri-cli   # Or follow Tauri's setup: https://tauri.app/v1/guides/getting-started/prerequisites
   

5. *Build and Run the Application*
   From the project root:
   
   cargo tauri dev     # For development mode (hot-reload)
   
   Or for a production build:
   
   cargo tauri build   # Creates installers in src-tauri/target/release/bundle
   

   - On first run, Tauri may prompt to install additional platform-specific tools (e.g., WebView2 on Windows).

### Usage After Installation
- Run cargo tauri dev to launch the app.
- Import your photo folders — the app will analyze images for objects, faces, and sort/cluster them privately (all processing is local).

### Troubleshooting
- If you encounter errors with OpenCV (e.g., libGL.so.1 missing), install the system libraries mentioned above.
- Check the GitHub Issues/Discussions for common problems: [GitHub Issues/Discussions](https://github.com/AOSSIE-Org/PictoPy/issues)
- Documentation may be limited; refer to Tauri's docs for build issues: [Tauri docs](https://tauri.app/)

### Alternative: Documentation Site
There is a project page at [project page](https://aossie-org.github.io/PictoPy/) — check there for updated guides or screenshots.

This guide is based on the standard setup for Tauri + Python projects like PictoPy. If the repository structure changes, refer directly to the README.md on GitHub.

Enjoy your privacy-focused photo gallery! If you run into specific errors, share them on the repo's Discussions. 🚀


Our Code of Conduct: [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
