# Rust Backend Setup

## Prerequisites

Before setting up the frontend, ensure you have the following installed:

- [Node.js](https://nodejs.org/) (LTS version recommended)
- npm (comes with Node.js)
- [Rust](https://www.rust-lang.org/tools/install) (latest stable version)
- [Tauri CLI](https://v2.tauri.app/start/prerequisites/)

For a comprehensive guide on prerequisites, refer to the [Tauri Prerequisites](https://v2.tauri.app/start/prerequisites/) documentation.

## Setup Directory

!!! note "Base Directory"
All commands executed below are with respect to the `frontend/` directory

### Installing Dependencies

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install the project dependencies:
   ```bash
   npm install
   ```

For more information on npm commands, see the [npm documentation](https://docs.npmjs.com/).

## Running the Application

To start the Tauri application in development mode, run:

```bash
npm run tauri dev
```

This command will:

- Start the [Vite](https://vitejs.dev/) development server for the frontend
- Compile the Rust backend
- Launch the Tauri application window

For more details on Tauri commands, check the [Tauri CLI documentation](https://tauri.app/v1/api/cli).

!!! note "First Run"
The first run might take longer as it needs to compile the Rust code.
