# PictoPy Features

!!! note "Gallery Applicaiton" - Smart tagging of photos based on detected objects, faces and their recognition - Traditional gallery features of album management.

!!! tip "Advanced Image Analysis" - Object detection using YOLOv8, enabling identification of various items in photos - Facial recognition powered by FaceNet, allowing for face detection and clustering

!!! success "Privacy-Focused Design" - Offline functionality ensuring user data remains on the local machine - No reliance on remote servers for image processing or analysis - Models are stored locally and can be changed according to user needs

!!! abstract "Data Handling and Parallel Processing" - Utilizes SQLite databases for lightweight and efficient storage of photo metadata, face embeddings, and album information - Implements background processing for handling large volumes of images without impacting user experience - Uses `asyncio` in the back to process images without blocking the frontend

!!! example "Smart Search and Retrieval" - Enables searching for photos based on detected objects, faces, or other metadata - Supports finding related images based on facial similarity or content

!!! info "Cross-Platform Compatibility" - Designed to work across different operating systems

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
| State Management  | React Hooks          |
| Styling           | Tailwind CSS         |
| Routing           | React Router         |
| UI Components     | Radix UI             |
| Build Tool        | Vite                 |
| Type Checking     | TypeScript           |
