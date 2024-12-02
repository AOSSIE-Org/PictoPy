# Backend Docker Setup for PictoPy

This guide provides step-by-step instructions for building and running the PictoPy backend using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Building the Docker Image](#building-the-docker-image)
3. [Running the Docker Container](#running-the-docker-container)
4. [Verifying the Container](#verifying-the-container)
5. [Accessing the Application](#accessing-the-application)
6. [Stopping the Container](#stopping-the-container)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the Docker installed on your machine

- Verify the installation by running:
  ```bash
  docker --version
  ```

## Building the Docker Image

1. Open a terminal and navigate to your project's root directory.

2. Go to Backend directory

   ```bash
   cd backend
   ```

3. Run the following command to build the Docker image, replacing `<image_name>` with your desired image name:

   ```bash
   docker build -t <image_name> .
   ```

4. Wait for the build process to complete. This may take a few minutes depending on your internet speed and system performance.

## Running the Docker Container

Once the image is built, you can run a container using the following command:

```bash
docker run -d -p 8000:8000 --name <container_name>  <image_name>
```

- `-d`: Runs the container in detached mode (in the background).
- `-p 8000:8000`: Maps port 8000 on the host to port 8000 in the container.
- `--name <container_name>`: Names the container for easier management.
- `<image_name>`: Specifies the image to use (the one we just built).

## Verifying the Container

To check if the container is running:

```bash
docker ps
```

You should see an entry for `<container_name>` with the status `Up`.

## Accessing the Application

Open a web browser or frontend to access the application at:

```
http://localhost:8000
```

## Stopping the Container

If you need to stop the container:

```bash
docker kill <container_id>
```

## Troubleshooting

1. **Port already in use**: If you get an error saying the port is already in use, you can either:

   - Stop the process using port 8000, or
   - Change the port mapping in the `docker run` command (e.g., `-p 8001:8000`)

2. **Container exits immediately**: Check the container logs:

   ```bash
   docker logs <container_name>
   ```

3. **Permission issues**: Ensure that `run.sh` has execute permissions(for linux only):

   ```bash
   chmod +x run.sh
   ```

   Then rebuild the Docker image.

Remember to rebuild your Docker image (`docker build -t <image_name> .`) after making any changes to your application or Dockerfile.

For more advanced Docker usage , view the [Docker documentation](https://docs.docker.com/get-started/).
