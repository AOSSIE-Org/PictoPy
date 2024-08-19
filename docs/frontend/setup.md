# Frontend Setup

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

## Building for Production

To create a production build of your Tauri application:

```bash
npm run tauri build
```

This will create an optimized build of your application in the `src-tauri/target/release` directory.

Learn more about building Tauri apps in the [Tauri Building Guide](https://tauri.app/v1/guides/building/).

## Troubleshooting

If you encounter any issues during setup or running the application:

1. Ensure all prerequisites are correctly installed.
2. Check that you're in the correct directory (`frontend/`).
3. Try deleting the `node_modules` folder and `package-lock.json` file, then run `npm install` again.
4. If Rust-related errors occur, try running `rustup update` to ensure you have the latest version.

For more detailed troubleshooting, refer to the [Tauri Troubleshooting Guide](https://tauri.app/v1/guides/debugging/debugging/).

## Additional Resources

- [Tauri Documentation](https://tauri.app/v1/guides/)
- [Vite Documentation](https://vitejs.dev/guide/)
- [React Documentation](https://reactjs.org/docs/getting-started.html) 
- [TypeScript Documentation](https://www.typescriptlang.org/docs/) 
- [Rust Book](https://doc.rust-lang.org/book/) 

By following these steps, you should have your Tauri frontend environment set up and ready for development. Remember to run `npm run tauri dev` to start your development environment.

