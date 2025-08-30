import React from 'react';

const BrowserWarning: React.FC = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-6 dark:bg-gray-900">
      <div className="mx-auto max-w-2xl rounded-lg border-l-4 border-yellow-500 bg-white p-8 text-center shadow-lg dark:bg-gray-800">
        <div className="mb-6">
          <svg
            className="mx-auto mb-4 h-16 w-16 text-yellow-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          <h1 className="mb-2 text-3xl font-bold text-gray-900 dark:text-white">
            PictoPy Desktop Required
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            This application is designed to run as a desktop app using Tauri.
          </p>
        </div>

        <div className="mb-6 rounded-lg bg-gray-50 p-6 dark:bg-gray-700">
          <h2 className="mb-3 text-xl font-semibold text-gray-900 dark:text-white">
            To run PictoPy:
          </h2>
          <div className="text-left">
            <p className="mb-3 text-gray-700 dark:text-gray-300">
              1. Open your terminal in the project directory
            </p>
            <p className="mb-3 text-gray-700 dark:text-gray-300">
              2. Navigate to the frontend folder:
            </p>
            <code className="mb-3 block rounded bg-black p-3 font-mono text-sm text-green-400">
              cd frontend
            </code>
            <p className="mb-3 text-gray-700 dark:text-gray-300">
              3. Run the desktop application:
            </p>
            <code className="block rounded bg-black p-3 font-mono text-lg font-bold text-green-400">
              npm run tauri dev
            </code>
          </div>
        </div>

        <div className="text-sm text-gray-500 dark:text-gray-400">
          <p>
            Note: PictoPy requires desktop capabilities for file system access,
            native dialogs, and other desktop features that aren't available in
            browsers.
          </p>
        </div>
      </div>
    </div>
  );
};

export default BrowserWarning;
