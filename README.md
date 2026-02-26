<!-- Don't delete it -->
<div name="readme-top"></div>

<!-- Organization Logo -->
<div align="center" style="display: flex; align-items: center; justify-content: center; gap: 16px;">
  <a href="https://aossie.org">
    <img src="https://aossie.org/logo1.png" alt="AOSSIE Logo" width="200"/>
  </a>
</div>

&nbsp;

<!-- Organization Name -->
<div align="center">

[![Static Badge](https://img.shields.io/badge/aossie.org/PictoPy-228B22?style=for-the-badge&labelColor=FFC517)](https://aossie.org/)

</div>

<!-- Organization/Project Social Handles -->
<p align="center">
  <!-- Email -->
    <a href="mailto:aossie.oss@gmail.com" title="Email">
      <img src="https://img.shields.io/badge/Email-D14836?style=flat&logo=gmail&logoColor=white" alt="Email"/>
  </a>
<!-- Telegram -->
<a href="https://t.me/StabilityNexus">
<img src="https://img.shields.io/badge/Telegram-black?style=flat&logo=telegram&logoColor=white&logoSize=auto&color=24A1DE" alt="Telegram Badge"/></a>
&nbsp;&nbsp;
<!-- X (formerly Twitter) -->
<a href="https://x.com/aossie_org">
<img src="https://img.shields.io/twitter/follow/aossie_org" alt="X (formerly Twitter) Badge"/></a>
&nbsp;&nbsp;
<!-- Discord -->
<a href="https://discord.gg/hjUhu33uAn">
<img src="https://img.shields.io/discord/1022871757289422898?style=flat&logo=discord&logoColor=white&logoSize=auto&label=Discord&labelColor=5865F2&color=57F287" alt="Discord Badge"/></a>
&nbsp;&nbsp;
<!-- Medium -->
<a href="https://news.stability.nexus/">
  <img src="https://img.shields.io/badge/Medium-black?style=flat&logo=medium&logoColor=black&logoSize=auto&color=white" alt="Medium Badge"></a>
&nbsp;&nbsp;
<!-- LinkedIn -->
<a href="https://www.linkedin.com/company/aossie/">
  <img src="https://img.shields.io/badge/LinkedIn-black?style=flat&logo=LinkedIn&logoColor=white&logoSize=auto&color=0A66C2" alt="LinkedIn Badge"></a>
&nbsp;&nbsp;
<!-- Youtube -->
<a href="https://www.youtube.com/@AOSSIE-Org">
  <img src="https://img.shields.io/youtube/channel/subscribers/UCKVVLbawY7Gej_3o2WKsoiA?style=flat&logo=youtube&logoColor=white&logoSize=auto&labelColor=FF0000&color=FF0000" alt="Youtube Badge"></a>
</p>

---

<div align="center">
<h1>PictoPy</h1>
</div>

PictoPy is an advanced desktop gallery application that combines the power of **Tauri**, **React**, and **Rust** for the frontend with a **Python** backend for sophisticated image analysis and management. It offers efficient data handling, parallel processing, and a privacy-focused design that keeps your data entirely offline.

---

## 🚀 Features

- **Smart Tagging**: Automatic tagging of photos based on detected objects, faces, and their recognition.
- **Album Management**: Traditional gallery features for organizing and managing photo albums.
- **Advanced Image Analysis**: Object detection and facial recognition powered by YOLO and FaceNet.
- **Privacy-Focused**: Fully offline functionality keeping your data on your device.
- **Smart Search & Retrieval**: Efficient search across your photo library.
- **Performance**: Efficient data handling and parallel processing for smooth operations.
- **Cross-Platform**: Compatible across major desktop operating systems.

---

## 💻 Tech Stack

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
| Clustering        | DBSCAN               |
| API Framework     | FastAPI              |
| State Management  | Redux Toolkit        |
| Styling           | Tailwind CSS         |
| Routing           | React Router         |
| UI Components     | ShadCN               |
| Build Tool        | Vite                 |
| Type Checking     | TypeScript           |

---

## 🏗️ Architecture

### Frontend
- **Tauri**: Enables building the secure, lightweight desktop application.
- **React**: Used for creating the dynamic user interface.
- **Rust**: Powers the system-level backend, which the frontend communicates with through Tauri's API.

### Backend (Python)
- **FastAPI**: Serves as the high-performance API framework.
- **SQLite**: Database for storing metadata and embeddings.
- **YOLO**: Used for precise object detection.
- **FaceNet**: Generates face embeddings for recognition.
- **ONNX Runtime**: Runs the ML models efficiently.
- **DBSCAN**: Performs clustering for face embeddings to group similar faces.

### Backend (Rust via Tauri)
Handles file system operations and provides a secure bridge between the frontend and the local system.

---

## 🔗 Repository Links

1. [Main Repository](https://github.com/AOSSIE-Org/PictoPy)
2. [Frontend](https://github.com/AOSSIE-Org/PictoPy/tree/main/frontend)
3. [Backend](https://github.com/AOSSIE-Org/PictoPy/tree/main/backend)

---
Copyright (C) 2026 AOSSIE (Australian Open Source Software Innovation and Education)

