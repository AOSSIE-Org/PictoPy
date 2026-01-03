import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

import threading
import atexit
import httpx
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Global tracking for subprocess log threads
_log_threads = []

# Global reference to the sync microservice process
_sync_process: Optional[subprocess.Popen] = None

# Sync service URL
SYNC_SERVICE_URL = "http://localhost:8001"


def cleanup_log_threads():
    """Clean up log threads during shutdown to ensure all buffered logs are processed."""
    if _log_threads:
        logger.info("Cleaning up log threads...")
        for thread in _log_threads:
            if thread.is_alive():
                thread.join(timeout=2.0)  # Wait up to 2 seconds for each thread
        _log_threads.clear()
        logger.info("Log threads cleanup completed")


# Register cleanup function to run at exit
atexit.register(cleanup_log_threads)


def microservice_util_stop_sync_service(timeout: float = 5.0) -> bool:
    """
    Stop the sync microservice gracefully via HTTP, with force-kill fallback.

    This function:
    1. Sends HTTP POST to /api/v1/shutdown endpoint
    2. Waits for the process to exit
    3. Force-kills if timeout exceeded

    Args:
        timeout: Maximum seconds to wait for graceful shutdown

    Returns:
        bool: True if service was stopped successfully
    """
    global _sync_process

    logger.info("Stopping sync microservice...")

    import time

    start_time = time.time()

    # Try graceful HTTP shutdown first
    http_timeout = min(timeout, 3.0)  # HTTP request timeout
    try:
        logger.info("Sending shutdown request to sync microservice...")
        with httpx.Client(timeout=http_timeout) as client:
            response = client.post(f"{SYNC_SERVICE_URL}/api/v1/shutdown")
            if response.status_code == 200:
                logger.info("Sync microservice acknowledged shutdown request")
    except httpx.TimeoutException:
        logger.warning("Timeout waiting for sync microservice shutdown response")
    except httpx.ConnectError:
        logger.info("Sync microservice not reachable (may already be stopped)")
    except Exception as e:
        logger.warning(f"Error sending shutdown request to sync: {e}")

    # Wait for process to exit if we have a reference
    if _sync_process is not None:
        try:
            # Give the sync service a moment to process the shutdown
            time.sleep(0.3)

            # Wait for process to exit gracefully (use remaining timeout)
            elapsed = time.time() - start_time
            wait_timeout = max(timeout - elapsed, 1.0)
            exit_code = _sync_process.wait(timeout=wait_timeout)
            logger.info(f"Sync microservice exited with code: {exit_code}")
            _sync_process = None
        except subprocess.TimeoutExpired:
            logger.warning(
                f"Sync microservice did not exit within {wait_timeout}s, force killing..."
            )
            _force_kill_sync_process()

    # Clean up log threads
    cleanup_log_threads()

    logger.info("Sync microservice stopped")
    return True


def _force_kill_sync_process():
    """
    Force kill the sync microservice process.
    Platform-specific implementation for Windows, macOS, and Linux.
    """
    global _sync_process

    if _sync_process is None:
        return

    try:
        pid = _sync_process.pid
        logger.warning(f"Force killing sync microservice (PID: {pid})...")

        system = platform.system().lower()

        if system == "windows":
            # Use taskkill with /T to kill child processes too
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                timeout=5,
            )
        else:
            # Unix/Linux/macOS - kill process group
            import signal

            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                # Process already dead or we don't have permission
                _sync_process.kill()

        logger.info("Sync microservice force killed")
    except Exception as e:
        logger.error(f"Error force killing sync microservice: {e}")
    finally:
        _sync_process = None


def microservice_util_is_sync_running() -> bool:
    """
    Check if the sync microservice is currently running.

    Returns:
        bool: True if running, False otherwise
    """
    global _sync_process

    if _sync_process is not None and _sync_process.poll() is None:
        return True

    # Also check via HTTP health endpoint
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{SYNC_SERVICE_URL}/api/v1/health")
            return response.status_code == 200
    except Exception:
        return False


def microservice_util_get_sync_process() -> Optional[subprocess.Popen]:
    """
    Get the sync microservice process reference.

    Returns:
        The subprocess.Popen object if running, None otherwise
    """
    global _sync_process
    return _sync_process


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


CYAN = "\033[96m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


def stream_logs(pipe, prefix, color):
    """Read a process pipe and print formatted logs from sync-microservice."""
    for line in iter(pipe.readline, ""):
        if line:
            # Trim any trailing newlines
            line = line.strip()
            if line:
                # All output from sync-microservice is now properly formatted by its logger
                print(line)
    pipe.close()


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
        cmd = str(sync_executable)  # Correct the command to use the actual path
        logger.info(f"Starting sync microservice with command: {cmd}")

        # Prepare subprocess arguments for process group creation
        kwargs = {}
        if system == "windows":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered output
            **kwargs,
        )

        # Start background threads to forward output to logger
        # Stream stdout with consistent SYNC-MICROSERVICE prefix
        t1 = threading.Thread(
            target=stream_logs,
            args=(process.stdout, "SYNC-MICROSERVICE", CYAN),
            daemon=False,
        )

        # Stream stderr with consistent SYNC-MICROSERVICE-ERR prefix
        t2 = threading.Thread(
            target=stream_logs,
            args=(process.stderr, "SYNC-MICROSERVICE-ERR", RED),
            daemon=False,
        )

        t1.start()
        t2.start()
        _log_threads.extend([t1, t2])

        # Store the process reference globally for shutdown
        global _sync_process
        _sync_process = process

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

        # Command to start FastAPI server
        logger.debug(f"Using Python executable: {python_executable}")
        host = "127.0.0.1"  # Local connections only for security
        port = "8001"

        # Basic uvicorn command that works on all platforms
        cmd = [
            str(python_executable),
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            host,
            "--port",
            port,
        ]

        logger.info(f"Executing command: {' '.join(cmd)}")

        # Prepare subprocess arguments for process group creation
        kwargs = {}
        if platform.system().lower() == "windows":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        # Start the process (non-blocking)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered output
            **kwargs,
        )

        # Start background threads to forward output to logger
        t1 = threading.Thread(
            target=stream_logs,
            args=(process.stdout, "SYNC-MICROSERVICE", CYAN),
            daemon=False,
        )

        t2 = threading.Thread(
            target=stream_logs,
            args=(process.stderr, "SYNC-MICROSERVICE-ERR", RED),
            daemon=False,
        )

        t1.start()
        t2.start()
        _log_threads.extend([t1, t2])

        # Store the process reference globally for shutdown
        global _sync_process
        _sync_process = process

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
