
# Docker Compose Setup

This repository includes a Docker Compose configuration to streamline the deployment of services for your application. By using Docker Compose, you can set up and run the entire stack with just a few commands.

## Prerequisites

Before you proceed, ensure the following tools are installed on your system:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

You can verify the installations by running:

```bash
docker --version
docker-compose --version
```

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


