# GSoC 2024 Report - PictoPy

## Project Overview

PictoPy is a project developed during Google Summer of Code 2024 for AOSSIE. The goal was to create a backend system for image processing, object detection, and face recognition.

## Phase 1 (Mid-Phase)

### Setup and Initial Development

1. **Backend Setup**
    - Initialized a FastAPI backend with a standard directory structure
    - Faced challenges with large library sizes for object detection models
    - Switched to ONNX format, reducing environment size from 5GB (with PyTorch GPU) to ~400MB

    !!! note "Related PRs"
        - [PR-25](https://github.com/AOSSIE-Org/PictoPy/pull/25) (Merged)
        - [PR-26](https://github.com/AOSSIE-Org/PictoPy/pull/26) (Closed)

2. **Routing Logic with Parallel Processing**
    - Implemented non-blocking requests using FastAPI
    - Explored various options for parallel processing (threading, multiprocessing)
    - Settled on asyncio for concurrent processing of multiple images
    - Switched from uvicorn to hypercorn for better cross-platform compatibility

3. **Database Design**
    - Developed schemas for storing image and album information
    - Image schema includes file path, object detection results, metadata, and potential face embeddings
    - Album schema contains multiple images and album-specific information
    - Plans to refine schemas for more concrete mappings and handle edge cases

    !!! note "Related PRs"
        - [PR-29](https://github.com/AOSSIE-Org/PictoPy/pull/29) (Merged)
        - [PR-30](https://github.com/AOSSIE-Org/PictoPy/pull/30) (Merged)


## Phase 2 (Final Phase)

### Feature Implementation

1. **Face Embeddings**
    - Integrated object detection model
    - Implemented face detection and embedding generation
    - Tested various models (ArcFace, VGG, etc.)
    - Selected FaceNet for optimal size and performance constraints
    - Used ultralytics model for object and face detection
    - Generated face embeddings using FaceNet
    - All models converted to ONNX format for efficiency

    !!! note "Related PR"
        [PR-34](https://github.com/AOSSIE-Org/PictoPy/pull/34) (Merged)

2. **Face Recognition and Schema Updates**
    - Implemented face clustering using DBSCAN algorithm
    - Updated schemas to accommodate clustering results
    - Ensured proper handling of image operations (add/delete) affecting clusters
    - Completed core project requirements (image database, album database, object detection, face detection, and recognition)
    - Optimized DBSCAN parameters for ONNX model performance

    !!! note "Related PR"
        [PR-36](https://github.com/AOSSIE-Org/PictoPy/pull/36) (Merged)

3. **Documentation and API Collection**
    - Created comprehensive documentation on setup, directory structure, and model architecture
    - Developed a [Postman Collection](https://www.postman.com/cryosat-explorer-62744145/workspace/pictopy/overview) for API testing and development
    - Utilized mkdocs-material for documentation, hosted [here](https://aossie-org.github.io/PictoPy/)
    - Provided a Dockerfile for backend containerization

    !!! note "Related PRs"
        - [PR-37](https://github.com/AOSSIE-Org/PictoPy/pull/37) (Closed)
        - [PR-39](https://github.com/AOSSIE-Org/PictoPy/pull/39) (Merged)
        - [PR-41](https://github.com/AOSSIE-Org/PictoPy/pull/41) (Merged)

### Project Completion Status

- **Status**: Completed
- **Significant Changes**: None, adhered to original plan with minor adjustments (e.g., using ONNX runtime instead of exploring OpenVINO)

## Future Plans

- Potential development of an Electron-based frontend
- Continued contribution to the project
- Promotion of PictoPy to leverage its potential and encourage further development

### Blog Posts

- [My GSoC Journey — The Beginning](https://medium.com/@mailbassam/my-gsoc-journey-phase-1-56664a0d6ba0)
- [My GSoC Journey — Phase 1](https://medium.com/@mailbassam/my-gsoc-journey-phase-1-14a6bf654799)
- [My GSoC Journey — Phase 2](https://medium.com/@mailbassam/my-gsoc-journey-phase-2-4eca00dfc8fc)
