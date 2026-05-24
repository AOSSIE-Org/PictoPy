# Manual Setup Guide

## Initial Steps

### 1. Fork the PictoPy repository: <https://github.com/AOSSIE-Org/PictoPy>

### 2. Open your Terminal (Linux/MacOS) or Powershell (Windows)

### 3. Clone your forked repository

```bash
git clone https://github.com/yourUsername/PictoPy
```

### 4. Change to the repository directory

```bash
cd PictoPy
```

### 5. Add the main repository as "upstream"

```bash
git remote add upstream https://github.com/AOSSIE-Org/PictoPy
```

## Prerequisites

### Install and Setup Miniconda

Before setting up the Python backend and sync-microservice, you need to have **Miniconda** installed and set up on your system.

1. **Download and Install Miniconda:**
   - Visit the [Miniconda installation guide](https://www.anaconda.com/docs/getting-started/miniconda/install#quickstart-install-instructions).
   - Follow the quickstart install instructions for your operating system.
   - Make sure `conda` is available in your terminal after installation.

2. **Verify Installation:**

   ```bash
   conda --version
   ```

   You should see the conda version number if installed correctly.

## Tauri Frontend Setup

1. **Install Tauri prerequisites based on your OS using this** [guide](https://tauri.app/start/prerequisites/).

2. **Navigate to the Frontend Directory:** Open your terminal and use `cd` to change directories:

   ```bash
   cd frontend
   ```

3. **Install Dependencies:**

   ```bash
   npm install
   ```

4. **Start the Tauri desktop app in development mode:**

   ```bash
   npm run tauri dev
   ```

## Python (FastAPI) Backend Setup Steps

> **Note:** For backend setup, make sure that you have **Miniconda installed**. See the Prerequisites section above. Additionally, for Windows, make sure that you are using Powershell for the setup, not Command Prompt.

1. **Navigate to the Backend Directory:** Open your terminal and use `cd` to change directories:

   ```bash
   cd backend
   ```

2. **Create a Conda Environment:** Create a new conda environment with Python 3.12:

   ```bash
   conda create -p .env python=3.12
   ```

3. **Activate the Conda Environment:**

   ```bash
   conda activate ./.env
   ```

4. **Install Dependencies:** The `requirements.txt` file lists required packages. Install them using pip:

   ```bash
   pip install -r requirements.txt
   ```

   > Local development keeps the CPU-only `onnxruntime` package. GPU acceleration is enabled per-platform in the release workflow, while the model recommendation step uses direct hardware detection instead of ONNX Runtime providers.

5. **Run the backend:** To start the backend in development mode, run this command while you are in the backend folder and the conda environment is activated:

   ```bash
   fastapi dev --port 52123
   ```

   The server will start on `http://localhost:52123` by default. In test mode, the server will automatically restart if any errors are detected or if source files are modified.

   ![Server running screenshot](/docs/assets/screenshots/serverRunning.png)

## Sync-Microservice Setup Steps

> **Note:** For sync-microservice setup, make sure that you have **Miniconda installed**. See the Prerequisites section above. Additionally, for Windows, make sure that you are using Powershell for the setup, not Command Prompt.

1. **Navigate to the Sync-Microservice Directory:** Open your terminal and use `cd` to change directories:

   ```bash
   cd sync-microservice
   ```

2. **Create a Conda Environment:** Create a new conda environment with Python 3.12:

   ```bash
   conda create -p .sync-env python=3.12
   ```

3. **Activate the Conda Environment:**

   ```bash
   conda activate ./.sync-env
   ```

4. **Install Dependencies:** The `requirements.txt` file lists required packages. Install them using pip:

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the sync-microservice:** To start the sync-microservice in development mode, run this command while you are in the sync-microservice folder and the conda environment is activated:

   ```bash
   fastapi dev --port 52124
   ```

   The server will start on `http://localhost:52124` by default. In development mode, the server will automatically restart if any errors are detected or if source files are modified.

## Troubleshooting Common Issues

1. **Missing System Dependencies:** Some dependencies might need system-level libraries like `libGL.so.1`, which is often needed by OpenCV. Install the appropriate packages based on your distribution:

   **Debian/Ubuntu:**

   ```bash
   sudo apt update
   sudo apt install -y libglib2.0-dev libgl1-mesa-glx
   ```

   **Other Systems:** Consult your distribution's documentation for installation instructions.

2. **`gobject-2.0` Not Found Error:** Resolve this error by installing `libglib2.0-dev` on Debian/Ubuntu:

   ```bash
   sudo apt install -y libglib2.0-dev pkg-config
   ```

   For other systems, consult your distribution's documentation.
