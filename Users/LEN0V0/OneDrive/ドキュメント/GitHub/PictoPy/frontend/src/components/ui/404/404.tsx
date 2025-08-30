// src\components\ui\404\404.tsx

import React from 'react';

interface NotFoundProps {
  message: string;
}

const NotFoundPage: React.FC<NotFoundProps> = ({ message }) => {
  return (
    <div className="flex min-h-[50vh] min-w-[90vh] flex-col items-center justify-center dark:bg-gray-900">
      <div className="w-full max-w-md px-4 text-center">
        <h1 className="mb-4 text-6xl font-bold text-gray-800 dark:text-gray-200">
          404
        </h1>
        <p className="mb-8 text-2xl text-gray-600 dark:text-gray-400">
          {message} Not Found
        </p>
        <a
          href="/"
          className="rounded inline-block bg-blue-500 px-6 py-3 text-white transition-colors hover:bg-blue-600"
        >
          Go Home
        </a>
      </div>
    </div>
  );
};

export default NotFoundPage;
