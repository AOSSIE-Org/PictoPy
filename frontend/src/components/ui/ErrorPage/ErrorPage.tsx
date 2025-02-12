import React from 'react';
import {FaRedoAlt } from 'react-icons/fa';


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
        <div className="min-h-screen flex shadow-lg shadow-gray-500 flex-col items-center justify-center  px-6 py-12">
            <div className="max-w-3xl w-full flex flex-col md:flex-row items-center justify-center bg-white p-8 rounded-lg shadow-xl space-y-8 md:space-y-0">
                <div className="text-center md:text-left space-y-6">
                    {/* Display the error code */}
                    <h1 className="text-6xl font-bold text-red-600">{errorCode}</h1>

                    {/* Display the error message */}
                    <h2 className="text-3xl font-semibold text-gray-800">{errorMessage}</h2>

                    {/* Display optional details, if provided */}
                    {details && <p className="text-lg text-gray-500 mt-2">{details}</p>}

                    <div className="mt-6 flex justify-center md:justify-start space-x-6">
                        {/* Show a retry button if an onRetry handler is provided */}
                        {onRetry && (
                            <button
                                onClick={onRetry}
                                className="inline-flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg shadow-md transition duration-300 ease-in-out"
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
