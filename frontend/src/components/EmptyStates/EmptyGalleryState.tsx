import { FolderOpen, Image as ImageIcon } from 'lucide-react';

export const EmptyGalleryState = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
        <FolderOpen className="h-16 w-16 text-gray-400" />
      </div>
      <h2 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
        No Images to Display
      </h2>
      <p className="mb-6 max-w-md text-gray-500 dark:text-gray-400">
        Your gallery is empty. Please add a folder containing images to get
        started.
      </p>
      <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
        <div className="flex items-center gap-2">
          <ImageIcon className="h-4 w-4" />
          <span>Supported formats: PNG, JPG, JPEG, GIF</span>
        </div>
        <div className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4" />
          <span>Go to Settings to add folders</span>
        </div>
      </div>
      <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
        <div className="flex items-center gap-2">
          <ImageIcon className="h-4 w-4" />
          <span>Supported formats: PNG, JPG, JPEG, GIF</span>
        </div>
        <div className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4" />
          <span>Go to Settings to add folders</span>
        </div>
      </div>
    </div>
  );
};
