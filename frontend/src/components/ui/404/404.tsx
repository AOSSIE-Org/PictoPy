// src\components\ui\404\404.tsx

import React from "react";

interface NotFoundProps {
  message: string;
}

const NotFoundPage: React.FC<NotFoundProps> = ({ message }) => {
  return (
    <div className="flex flex-col items-center justify-center min-w-[90vh] min-h-[50vh] dark:bg-gray-900">
      <div className="text-center max-w-md w-full px-4">
        <h1 className="text-6xl font-bold text-gray-800 dark:text-gray-200 mb-4">
          404
        </h1>
        <p className="text-2xl text-gray-600 dark:text-gray-400 mb-8">
          {message} Not Found
        </p>
        <a
          href="/"
          className="inline-block px-6 py-3 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Go Home
        </a>
      </div>
    </div>
  );
};

export default NotFoundPage;
