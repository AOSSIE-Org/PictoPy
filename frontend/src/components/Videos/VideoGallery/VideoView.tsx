import React, { useEffect, useState } from "react";

const VideoView: React.FC<{
  videos: string[];
  initialIndex: number;
  onClose: () => void;
}> = ({ videos, initialIndex, onClose }) => {
  const [currentvideoIndex, setCurrentvideoIndex] =
    useState<number>(initialIndex);

  useEffect(() => {
    setCurrentvideoIndex(initialIndex);
  }, [initialIndex]);

  function handlePrevvideo() {
    setCurrentvideoIndex((prevIndex) =>
      prevIndex === 0 ? videos.length - 1 : prevIndex - 1
    );
  }

  function handleNextvideo() {
    setCurrentvideoIndex((prevIndex) =>
      prevIndex === videos.length - 1 ? 0 : prevIndex + 1
    );
  }

  return (
    <div className="fixed top-0 left-0 w-full h-full flex justify-center items-center bg-black bg-opacity-90 z-50">
      <button
        onClick={onClose}
        className="absolute top-4 left-4 px-4 py-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-200"
      >
        Back
      </button>
      <video src={videos[currentvideoIndex]} className="max-h-full" controls />
      <button
        onClick={handlePrevvideo}
        className="absolute top-1/2 left-4 transform -translate-y-1/2 p-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-20"
      >
        {"<"}
      </button>
      <button
        onClick={handleNextvideo}
        className="absolute top-1/2 right-4 transform -translate-y-1/2 p-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-200"
      >
        {">"}
      </button>
    </div>
  );
};

export default VideoView;
