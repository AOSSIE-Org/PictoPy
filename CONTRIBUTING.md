# Contributing to This Project

Thank you for considering contributing to this project! This document outlines the setup and testing guidelines to help you get started.

---

## 🛠️ Setup Instructions

You can set up the project using one of the following approaches:




## Setup

1. Setup Using Script (Recommended Approach): [Guide](docs/Script_Setup_Guide.md)
2. Setup Manually: [Guide](docs/Manual_Setup_Guide.md)
3. Docker Setup:

   - Docker Compose Setup: [Guide](./docs/docker-compose/redme.md)
   - Setup using Dockerfile

     - For setting up the frontend, follow the instructions in the [Frontend Setup Guide](./docs/frontend/docker-setup.md).
       </br>
     - For setting up the backend, follow the instructions in the [Backend Setup Guide](./docs/backend/docker-setup.md).

## Testing

### Frontend

```bash
cd frontend
npm test
```

### Backend

- FastAPI
  ```bash
  cd backend
  pytest
  ```
- Tauri

  ```bash
  cd frontend/src-tauri/
  cargo test
  ```

## Building for Production

Create Signing Keys for tauri using the command:

```bash
npm run tauri signer generate
```

Set the public key in tauri.conf.json as pubkey and private key and password in Environment Variables as TAURI_SIGNING_PRIVATE_KEY and TAURI_SIGNING_PRIVATE_KEY_PASSWORD

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

## Additional Resources

- [Tauri Documentation](https://tauri.app/start/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Troubleshooting

If you encounter any issues, please check the respective documentation for Tauri, React, and FastAPI. For persistent problems, feel free to open an issue in the project repository.
