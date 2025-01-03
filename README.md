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

## Setup

### Frontend Setup

#### Prerequisites

- Node.js (LTS version recommended)
- npm (comes with Node.js)
- Rust (latest stable version)
- Tauri CLI

#### Installation


1. Clone the repository to your local system:
    ```bash
    git clone git@github.com:AOSSIE-Org/PictoPy.git
    ```
    ```bash
    cd PictoPy
    ```


1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

   ```bash
    cd scripts
   ```

    On Debian/Ubuntu:
    ```bash
    ./setup_env.sh
    ```
    On Windows:
    ```
    ./setup_win.ps1
    ```

#### Running the Application

```bash
npm run tauri dev
```

#### Building for Production

Create Signing Keys for tauri using the command:

```bash
npm run tauri signer generate
```

Set the public key in tauri.conf.json as pubkey and private key and password in Enviroment Variables as TAURI_SIGNING_PRIVATE_KEY and TAURI_SIGNING_PRIVATE_KEY_PASSWORD

There is a preset pubkey in tauri.conf.json ; private key and password for it is:

```bash
TAURI_SIGNING_PRIVATE_KEY=dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5NlF2SjE3cWNXOVlQQ0JBTlNITEpOUVoyQ3ZuNTdOSkwyNE1NN2RmVWQ1a0FBQkFBQUFBQUFBQUFBQUlBQUFBQU9XOGpTSFNRd0Q4SjNSbm5Oc1E0OThIUGx6SS9lWXI3ZjJxN3BESEh1QTRiQXlkR2E5aG1oK1g0Tk5kcmFzc0IvZFZScEpubnptRkxlbDlUR2R1d1Y5OGRSYUVmUGoxNTFBcHpQZ1dSS2lHWklZVHNkV1Byd1VQSnZCdTZFWlVGOUFNVENBRlgweUU9Cg==
```

```bash
TAURI_SIGNING_PRIVATE_KEY_PASSWORD=pass
```

```bash
npm run tauri build
```

### Python Backend Setup

#### Installation Steps

1.  **Navigate to the Backend Directory:** Open your terminal and use `cd` to change directories:

    Bash

    ```
    cd backend

    ```

2.  **Set Up a Virtual Environment (Highly Recommended):** Virtual environments isolate project dependencies. Create one using:

    Bash

    ```
    python -m venv venv  # Replace "venv" with your desired environment name

    ```

    Activate it for Linux/macOS:

    Bash

    ```
    source venv/bin/activate

    ```

    Activate it for Windows:

    Bash

    ```
    venv\Scripts\activate.bat

    ```

3.  **Install Dependencies:** The `requirements.txt` file lists required packages. Install them using pip:

    Bash

    ```
    pip install -r requirements.txt

    ```
    Note: python 3.13 and above are not compatible with this project currently.

4.  **Missing System Dependencies:** Some dependencies might need system-level libraries like `libGL.so.1` (often needed by OpenCV). Install the appropriate packages based on your distribution:

    **Debian/Ubuntu:**

    Bash

    ```
    sudo apt update
    sudo apt install -y libglib2.0-dev libgl1-mesa-glx

    ```

    **Other Systems:** Consult your distribution's documentation for installation instructions.

5.  **Permission Errors with `run.sh`:** If you encounter a "Permission denied" error when running `run.sh`, grant execute permissions:

    Bash

    ```
    chmod +x ./run.sh

    ```

6.  **`gobject-2.0` Not Found Error:** Resolve this error by installing `libglib2.0-dev` (Debian/Ubuntu):

    Bash

    ```
    sudo apt install -y libglib2.0-dev pkg-config

    ```

    For other systems, consult your distribution's documentation.

**Running the Backend**

Once installation and dependency resolution are complete, you can start the backend server:

**UNIX-based Systems (Linux, macOS):**

bash

```
./run.sh  # To run in production mode
./run.sh --test  # To run in testing mode
```

**Windows:**

Using PowerShell (Recommended):

powershell

```
.\run-server.ps1  # To run in production mode
.\run-server.ps1 --test  # To run in testing mode
```

Note: If you encounter a PowerShell execution policy error, run this command first:

powershell

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Alternative using Batch (Legacy):
bash

```
run.bat  # To run in production mode
run.bat --test # To run in testing mode
```

The server will start on `http://localhost:8000` by default. In test mode, the server will automatically restart if any errors are detected or if source files are modified.

You can control the number of workers by setting the `WORKERS` environment variable before running the script. If not set, it defaults to 1 worker.

### Docker Compose Setup
- [Docker Compose](./docs/docker-compose/redme.md)

### Setup using Dockerfile

- For setting up the frontend, follow the instructions in the [Frontend Setup Guide](./docs/frontend/docker-setup.md).
  </br>
- For setting up the backend, follow the instructions in the [Backend Setup Guide](./docs/backend/docker-setup.md).

## Additional Resources

- [Tauri Documentation](https://tauri.app/v1/guides/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Troubleshooting

If you encounter any issues, please check the respective documentation for Tauri, React, and FastAPI. For persistent problems, feel free to open an issue in the project repository.
