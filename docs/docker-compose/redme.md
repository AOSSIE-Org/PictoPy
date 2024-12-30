
# Docker Compose Setup

This repository includes a Docker Compose configuration to streamline the deployment of services for your application. By using Docker Compose, you can set up and run the entire stack with just a few commands.

## Prerequisites

Before you proceed, ensure the following tools are installed in your system:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

You can verify the installations by running:

```bash
docker --version
docker-compose --version
```

- For Linux : An X server also installed (If not installed)
    ```bash
    sudo apt install x
    ```
    Allow X11 forwarding:
    ```bash
    xhost +local:docker
    ```

- For Windows: An X Server (e.g., VcXsrv or Xming)
    - Start an X Server:
        1. Launch VcXsrv or Xming.
        2. Configure it to allow connections from any host.

    - Find your host machine's IP address:
        1. Open Command Prompt and run `ipconfig`.
        2. Look for the IPv4 Address under your active network adapter.

    - Run the container:
        ```bash
        docker run -it -p 1420:1420 -e DISPLAY=<HOST_IP>:0.0  <image-name>
        ```
        Replace `<HOST_IP>` with your actual IP address.





## Services

The Docker Compose file in this repository orchestrates the following services:

1. **Backend** : The application backend service.
4. **Frontend** : The application frontend service.

## Getting Started

### Step 1: Clone the Repository

Clone the repository to your local system:

```bash
git clone git@github.com:AOSSIE-Org/PictoPy.git
```

```bash
cd PictoPy
```

### Step 2: For resolving Line Ending problems in 'run.sh'

```bash
cd backend
dos2unix run.sh
```

### Step 3 : Move to Actual Location (PictoPy)
```bash
cd ..
```

### Step 3: Build and Start Services

Run the following command to build and start all services:

```bash
docker compose up --build
```

### Step 4: Access Services

- **Backend**: Accessible at `http://localhost:8000`
- **Frontend**: Accessible at `http://localhost:1420`

### Step 5: Stopping Services

To stop all running containers:

```bash
docker compose down
```

To stop services without removing the data:

```bash
docker compose stop
```


## How to 'Add Folder' Instructions

Since Docker containers are isolated from each other, we cannot directly access the folders of other containers. This is where the concept of volume mounting comes into play.where if you run your application via docker then for adding folders of your host machine
  
  1. Click the Path **Other Locations**
  2. Then click **Computer**
  3. After that click **host**
  
  (Genrally in Linux , **C** and **D** Drive are located in **mnt** folder)

Now in this **host** location all of your host machine's files are available now you can add any folder from this path .

At all if you face any problem Click the [Video Demo](https://s3.eu-north-1.amazonaws.com/jibeshroy.static.dev/Pictopy/FINAL_OUTPUT.mp4) 
