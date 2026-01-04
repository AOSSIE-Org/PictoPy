## Manual Setup Guide

### Initial Steps:

#### 1. Fork the PictoPy repository: https://github.com/AOSSIE-Org/PictoPy

#### 2. Open your Terminal (Linux/MacOS) or Powershell (Windows)

#### 3. Clone your forked repository:

```bash
git clone https://github.com/yourUsername/PictoPy
```

#### 4. Change to the repository directory:

```bash
cd PictoPy
```

#### 5. Add the main repository as "upstream":

```bash
git remote add upstream https://github.com/AOSSIE-Org/PictoPy
```

### Tauri Frontend Setup:

1. **Install Tauri prerequisites based on your OS using this** [guide](https://tauri.app/start/prerequisites/).

2. **Navigate to the Frontend Directory:** Open your terminal and use `cd` to change directories:
   ```
   cd frontend
   ```
3. **Install Dependencies**:
   ```
   npm install
   ```
4. **Start the Tauri desktop app in development mode**
   ```
   npm run tauri dev
   ```

### Python (FastAPI) Backend Setup Steps:

> **Note:** For backend setup make sure that you have **Python version 3.12**. Additionally, for Windows, make sure that you are using Powershell for the setup, not command prompt.

1.  **Navigate to the Backend Directory:** Open your terminal and use `cd` to change directories:

    Bash

    ```
    cd backend
    ```

2.  **Set Up a Virtual Environment (Highly Recommended):** Virtual environments isolate project dependencies. Create one using:

    Bash(Linux/MacOS)

    ```
    python3 -m venv .env
    ```

    Powershell(Windows)

    ```
    python -m venv .env
    ```

3.  **Activate the Virtual Environment:**

    Bash(Linux/MacOS)

    ```
    source .env/bin/activate
    ```

    Powershell(Windows)

    ```
    .env\Scripts\Activate.ps1
    ```

    After activating, you should be able to see the virtual environment's name before the current path. Something like this:

    ![alt text](/docs/assets/screenshots/virtualEnv.png)

4.  **Install Dependencies:** The `requirements.txt` file lists required packages. Install them using pip:

    Bash

    ```
    pip install -r requirements.txt
    ```

5.  **Running the backend:**: To start the backend in development mode, run this command while being in the backend folder and the virtual environment activated:

    Bash/Powershell

    ```
    fastapi dev --port 52123
    ```

    The server will start on `http://localhost:52123` by default. In test mode, the server will automatically restart if any errors are detected or if source files are modified.

    ![alt text](/docs/assets/screenshots/serverRunning.png)

### Sync-Microservice Setup Steps:

> **Note:** For sync-microservice setup make sure that you have **Python version 3.12**. Additionally, for Windows, make sure that you are using Powershell for the setup, not command prompt.

1.  **Navigate to the Sync-Microservice Directory:** Open your terminal and use `cd` to change directories:

    Bash

    ```
    cd sync-microservice
    ```

2.  **Set Up a Virtual Environment (Highly Recommended):** Virtual environments isolate project dependencies. Create one using:

    Bash(Linux/MacOS)

    ```
    python3 -m venv .sync-env
    ```

    Powershell(Windows)

    ```
    python -m venv .sync-env
    ```

3.  **Activate the Virtual Environment:**

    Bash(Linux/MacOS)

    ```
    source .sync-env/bin/activate
    ```

    Powershell(Windows)

    ```
    .sync-env\Scripts\Activate.ps1
    ```

    After activating, you should be able to see the virtual environment's name before the current path.

4.  **Install Dependencies:** The `requirements.txt` file lists required packages. Install them using pip:

    Bash

    ```
    pip install -r requirements.txt
    ```

5.  **Running the sync-microservice:** To start the sync-microservice in development mode, run this command while being in the sync-microservice folder and the virtual environment activated:

    Bash/Powershell

    ```
    fastapi dev --port 52124
    ```

    The server will start on `http://localhost:52124` by default. In development mode, the server will automatically restart if any errors are detected or if source files are modified.

### Troubleshooting Common Issues:

1.  **Missing System Dependencies:** Some dependencies might need system-level libraries like `libGL.so.1` (often needed by OpenCV). Install the appropriate packages based on your distribution:

    **Debian/Ubuntu:**

    Bash

    ```
    sudo apt update
    sudo apt install -y libglib2.0-dev libgl1-mesa-glx

    ```

    **Other Systems:** Consult your distribution's documentation for installation instructions.

2.  **`gobject-2.0` Not Found Error:** Resolve this error by installing `libglib2.0-dev` (Debian/Ubuntu):

    Bash

    ```
    sudo apt install -y libglib2.0-dev pkg-config

    ```

    For other systems, consult your distribution's documentation.
