import React from 'react';
import { useNavigate } from 'react-router-dom';
import { lineWobble } from 'ldrs';
import { ArrowLeft } from 'lucide-react';

lineWobble.register();

export const LoadingScreen: React.FC = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-900 bg-opacity-75">
      {/* Back Button */}
      <button
        onClick={handleBack}
        className="absolute left-4 top-4 flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-gray-900 shadow transition-all hover:bg-gray-100"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      {/* Loading Animation */}
      <l-line-wobble
        size="80"
        stroke="5"
        bg-opacity="0.1"
        speed="1.75"
        color="white"
      ></l-line-wobble>

      {/* Loading Text */}
      <p className="mt-4 animate-pulse text-lg font-semibold text-white">
        Loading...
      </p>
    </div>
  );
};

export default LoadingScreen;
