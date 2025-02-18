import React from "react";
import { useNavigate } from "react-router-dom";
import { lineWobble } from "ldrs";

lineWobble.register();

export const LoadingScreen: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-900 bg-opacity-75">
      {/* Conditionally Show Back Button Only If There’s History */}
      {window.history.length > 1 && (
        <button
          onClick={() => navigate(-1)}
          className="absolute top-4 left-4 flex items-center gap-2 rounded-lg bg-white px-4 py-2 font-semibold text-gray-900 shadow-md transition hover:bg-gray-200"
        >
          <span className="text-lg">←</span> Back
        </button>
      )}

      {/* Loading Animation */}
      <l-line-wobble size="80" stroke="5" bg-opacity="0.1" speed="1.75" color="white"></l-line-wobble>
      <p className="mt-4 animate-pulse text-lg font-semibold text-white">Loading...</p>
    </div>
  );
};

export default LoadingScreen;