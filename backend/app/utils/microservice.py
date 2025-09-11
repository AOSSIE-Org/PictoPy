import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

import logging

logger = logging.getLogger(__name__)


def microservice_util_start_sync_service(
    sync_service_path: Optional[str] = None,
) -> bool:
    """
    Start the sync microservice with automatic virtual environment management.

    When running as a frozen executable (PyInstaller), it will use the bundled
    PictoPy_Sync executable. Otherwise, it uses the development setup with venv.

    Args:
        sync_service_path: Path to the sync microservice directory.
                          If None, defaults to 'sync-microservice' relative to project root.

    Returns:
        bool: True if service started successfully, False otherwise.
    """
    try:
        # Check if running as a frozen executable (PyInstaller)
        if getattr(sys, "frozen", False):
            logger.info(
                "Running as frozen executable, using bundled sync microservice..."
            )
            return _start_frozen_sync_service()

        # Development mode - use virtual environment setup
        logger.info("Running in development mode, using virtual environment...")
        return _start_dev_sync_service(sync_service_path)

    except Exception as e:
        logger.error(f"Error starting sync microservice: {e}")
        return False


def _start_frozen_sync_service() -> bool:
    """
    Start the sync microservice when running as a frozen executable.
    The sync microservice executable should be in the PictoPy_Sync folder.
    """
    try:
        # Get the directory where the current executable is located
        if getattr(sys, "frozen", False):
            # When frozen, sys.executable points to the main executable
            app_dir = Path(sys.executable).parent.parent
        else:
            # Fallback (shouldn't happen in this function)
            app_dir = Path(__file__).parent.parent.parent.parent

        # Look for the sync-microservice directory and executable
        sync_dir = app_dir / "sync-microservice"

        # Determine executable name based on platform
        system = platform.system().lower()
        if system == "windows":
            sync_executable = sync_dir / "PictoPy_Sync.exe"
        else:
            sync_executable = sync_dir / "PictoPy_Sync"

        if not sync_executable.exists():
            logger.error(
                f"Sync microservice executable not found at: {sync_executable}"
            )
            return False

        logger.info(f"Starting sync microservice from: {sync_executable}")

        # Start the sync microservice executable
        process = subprocess.Popen(
            [str(sync_executable)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(sync_dir),  # Set working directory to sync service directory
        )

        logger.info(f"Sync microservice started with PID: {process.pid}")
        logger.info("Service should be available at http://localhost:8001")

        return True

    except Exception as e:
        logger.error(f"Error starting frozen sync microservice: {e}")
        return False


def _start_dev_sync_service(sync_service_path: Optional[str] = None) -> bool:
    """
    Start the sync microservice in development mode using virtual environment.
    """
    try:
        # Determine the sync service path
        if sync_service_path is None:
            # Get project root (assuming this file is in backend/app/utils/)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            sync_service_path = project_root / "sync-microservice"
        else:
            sync_service_path = Path(sync_service_path)

        if not sync_service_path.exists():
            logger.error(f"Sync service directory not found: {sync_service_path}")
            return False

        # Define virtual environment path
        venv_path = sync_service_path / ".sync-env"

        # Check if virtual environment exists
        if not venv_path.exists():
            logger.info("Virtual environment not found. Creating .sync-env...")
            if not _create_virtual_environment(venv_path):
                logger.error("Failed to create virtual environment")
                return False

        # Get the Python executable path from the virtual environment
        python_executable = _get_venv_python_executable(venv_path)
        if not python_executable:
            logger.error("Failed to locate Python executable in virtual environment")
            return False

        # Install dependencies if requirements.txt exists
        requirements_file = sync_service_path / "requirements.txt"
        if requirements_file.exists():
            logger.info("Installing dependencies...")
            if not _install_requirements(python_executable, requirements_file):
                logger.warning("Failed to install requirements, but continuing...")

        # Start the FastAPI service
        logger.info("Starting sync microservice on port 8001...")
        return _start_fastapi_service(python_executable, sync_service_path)

    except Exception as e:
        logger.error(f"Error starting dev sync microservice: {e}")
        return False


def _create_virtual_environment(venv_path: Path) -> bool:
    """Create a virtual environment at the specified path."""
    try:
        # Use the current Python interpreter to create the virtual environment
        cmd = [sys.executable, "-m", "venv", str(venv_path)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"Virtual environment created successfully at {venv_path}")
            return True
        else:
            logger.error(f"Failed to create virtual environment: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Virtual environment creation timed out")
        return False
    except Exception as e:
        logger.error(f"Error creating virtual environment: {e}")
        return False


def _get_venv_python_executable(venv_path: Path) -> Optional[Path]:
    """Get the Python executable path from the virtual environment."""
    system = platform.system().lower()

    if system == "windows":
        # Windows: .sync-env/Scripts/python.exe
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        # Unix/Linux/macOS: .sync-env/bin/python
        python_exe = venv_path / "bin" / "python"

    if python_exe.exists():
        return python_exe
    else:
        logger.error(f"Python executable not found at {python_exe}")
        return None


def _install_requirements(python_executable: Path, requirements_file: Path) -> bool:
    """Install requirements using pip in the virtual environment."""
    try:
        cmd = [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout for pip install
        )

        if result.returncode == 0:
            logger.info("Requirements installed successfully")
            return True
        else:
            logger.error(f"Failed to install requirements: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Requirements installation timed out")
        return False
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return False


def _start_fastapi_service(python_executable: Path, service_path: Path) -> bool:
    """Start the FastAPI service using the virtual environment Python."""
    try:
        # Change to the service directory
        original_cwd = os.getcwd()
        os.chdir(service_path)

        # Command to start FastAPI dev server
        print(python_executable)
        host = "127.0.0.1"
        port = "8001"
        # On Windows, use a different approach with scripts path

        if platform.system().lower() == "windows":
            # Use uvicorn directly to run the FastAPI app
            cmd = [
                str(python_executable),
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                host,
                "--port",
                port,
                "--reload",  # Add reload flag for development convenience
            ]
        else:
            # For non-Windows platforms
            cmd = [str(python_executable), "-m", "fastapi", "dev", "--port", "8001"]

        logger.info(f"Executing command: {' '.join(cmd)}")

        # Start the process (non-blocking)
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Restore original working directory
        os.chdir(original_cwd)

        logger.info(f"Sync microservice started with PID: {process.pid}")
        logger.info("Service should be available at http://localhost:8001")

        return True

    except Exception as e:
        logger.error(f"Error starting FastAPI service: {e}")
        # Restore original working directory in case of error
        try:
            os.chdir(original_cwd)
        except Exception:
            pass
        return False
