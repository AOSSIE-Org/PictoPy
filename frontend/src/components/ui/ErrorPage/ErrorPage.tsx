import React from 'react';
import { FaRedoAlt } from 'react-icons/fa';

interface ErrorPageProps {
  errorCode?: number; // Optional error code, defaults to 404
  errorMessage?: string; // Optional error message
  details?: string; // Optional additional details (string)
  onRetry?: () => void; // Optional retry handler for recoverable errors
}

const ErrorPage: React.FC<ErrorPageProps> = ({
  errorCode = 404, // Default error code
  errorMessage = "The page you're looking for doesn't exist or is unavailable.",
  details, // Optional detailed message
  onRetry, // Optional retry handler for recoverable errors
}) => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12 shadow-lg shadow-gray-500">
      <div className="flex w-full max-w-3xl flex-col items-center justify-center space-y-8 rounded-lg bg-white p-8 shadow-xl md:flex-row md:space-y-0">
        <div className="space-y-6 text-center md:text-left">
          {/* Display the error code */}
          <h1 className="text-6xl font-bold text-red-600">{errorCode}</h1>

          {/* Display the error message */}
          <h2 className="text-3xl font-semibold text-gray-800">
            {errorMessage}
          </h2>

          {/* Display optional details, if provided */}
          {details && <p className="mt-2 text-lg text-gray-500">{details}</p>}

          <div className="mt-6 flex justify-center space-x-6 md:justify-start">
            {/* Show a retry button if an onRetry handler is provided */}
            {onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center rounded-lg bg-green-600 px-6 py-3 font-semibold text-white shadow-md transition duration-300 ease-in-out hover:bg-green-700"
              >
                <FaRedoAlt className="mr-2 text-xl" />
                Reload
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorPage;
