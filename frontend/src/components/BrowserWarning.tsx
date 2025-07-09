import React from 'react';

const BrowserWarning: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-6">
      <div className="max-w-2xl mx-auto text-center bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 border-l-4 border-yellow-500">
        <div className="mb-6">
          <svg 
            className="mx-auto h-16 w-16 text-yellow-500 mb-4" 
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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            PictoPy Desktop Required
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            This application is designed to run as a desktop app using Tauri.
          </p>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
            To run PictoPy:
          </h2>
          <div className="text-left">
            <p className="text-gray-700 dark:text-gray-300 mb-3">
              1. Open your terminal in the project directory
            </p>
            <p className="text-gray-700 dark:text-gray-300 mb-3">
              2. Navigate to the frontend folder:
            </p>
            <code className="block bg-black text-green-400 p-3 rounded mb-3 font-mono text-sm">
              cd frontend
            </code>
            <p className="text-gray-700 dark:text-gray-300 mb-3">
              3. Run the desktop application:
            </p>
            <code className="block bg-black text-green-400 p-3 rounded font-mono text-lg font-bold">
              npm run tauri dev
            </code>
          </div>
        </div>
        
        <div className="text-sm text-gray-500 dark:text-gray-400">
          <p>
            Note: PictoPy requires desktop capabilities for file system access, 
            native dialogs, and other desktop features that aren't available in browsers.
          </p>
        </div>
      </div>
    </div>
  );
};

export default BrowserWarning; 