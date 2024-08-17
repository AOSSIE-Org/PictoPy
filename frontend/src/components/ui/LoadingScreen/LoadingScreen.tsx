import React from "react";
import { lineWobble } from "ldrs";

lineWobble.register();

export const LoadingScreen: React.FC = () => (
  <div className="fixed inset-0 flex flex-col justify-center items-center bg-gray-900 bg-opacity-75 z-50">
    <l-line-wobble
      size="80"
      stroke="5"
      bg-opacity="0.1"
      speed="1.75"
      color="white"
    ></l-line-wobble>
    <p className="mt-4 text-white text-lg font-semibold animate-pulse">
      Loading...
    </p>
  </div>
);

export default LoadingScreen;
