# Docker Setup for PictoPy Frontend

This guide provides instructions for building and running the PictoPy frontend using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Building the Docker Image](#building-the-docker-image)
3. [Running the Container](#running-the-container)
   - [Linux](#linux)
   - [Windows](#windows)
4. [Accessing the GUI App](#accessing-the-gui-app)
5. [Common Troubleshooting](#common-troubleshooting)
6. [Notes on Cross-Platform Compatibility](#notes-on-cross-platform-compatibility)

## Prerequisites

- Docker installed on your system
- For Windows: An X Server (e.g., VcXsrv or Xming)
- For Linux : An X server also installed
  ```bash
  sudo apt install x
  ```

## Building the Docker Image

1. Open a terminal and navigate to your project's root directory.

2. Go to Frontend directory

   ```bash
   cd frontend
   ```

3. Run the following command to build the Docker image, replacing `<image_name>` with your desired image name:

   ```bash
   docker build --build-arg TAURI_SIGNING_PRIVATE_KEY=<private_key> --build-arg TAURI_SIGNING_PRIVATE_KEY_PASSWORD=<password> -t <image_name> .
   ```

   Replace <private_key> and <password> with your actual Tauri signing private key and password and <image_name> with the image name. If you are using the default key, you can use the following command:

   ```bash
   docker build --build-arg TAURI_SIGNING_PRIVATE_KEY=dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5NlF2SjE3cWNXOVlQQ0JBTlNITEpOUVoyQ3ZuNTdOSkwyNE1NN2RmVWQ1a0FBQkFBQUFBQUFBQUFBQUlBQUFBQU9XOGpTSFNRd0Q4SjNSbm5Oc1E0OThIUGx6SS9lWXI3ZjJxN3BESEh1QTRiQXlkR2E5aG1oK1g0Tk5kcmFzc0IvZFZScEpubnptRkxlbDlUR2R1d1Y5OGRSYUVmUGoxNTFBcHpQZ1dSS2lHWklZVHNkV1Byd1VQSnZCdTZFWlVGOUFNVENBRlgweUU9Cg== --build-arg TAURI_SIGNING_PRIVATE_KEY_PASSWORD=pass -t <image_name> .
   ```

## Running the Container

### Linux

1. Allow X11 forwarding:

   ```bash
   xhost +local:docker
   ```

2. Run the container:

   ```bash
   docker run -it -p 1420:1420 -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix <image_name>
   ```

3. Run the tauri application
   ```bash
   npm run tauri dev
   ```

### Windows

1. Start an X Server:

   - Launch VcXsrv or Xming.
   - Configure it to allow connections from any host.

2. Find your host machine's IP address:

   - Open Command Prompt and run `ipconfig`.
   - Look for the IPv4 Address under your active network adapter.

3. Run the container:

   ```bash
   docker run -it -p 1420:1420 -e DISPLAY=<HOST_IP>:0.0  <image-name>
   ```

Replace `<HOST_IP>` with your actual IP address.

4.  Run the tauri application
    ```bash
    npm run tauri dev
    ```

## Accessing the GUI App

If everything is configured correctly, the Tauri GUI app should display on your screen after running the container.

## Common Troubleshooting

### 1. GUI Not Displaying (X Server Issues)

- **Windows**:

  - Ensure the X server (VcXsrv or Xming) is running.
  - Check that it's configured to allow connections from any host.

- **Linux**:
  - Verify X11 forwarding is allowed: `xhost +local:docker`

### 2. Network Issues

If the container can't connect to the X server:

1. Check your firewall settings and ensure it's not blocking the connection.
2. On Windows, try using the host's IP address instead of localhost.

By following this guide and keeping these notes in mind, you should be able to successfully set up and run the PictoPy frontend using Docker across different platforms. If you encounter any persistent issues, please refer to the project's issue tracker or seek assistance from the development team.
