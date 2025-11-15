import { FolderPlus, BookImage } from 'lucide-react';

export const EmptyAlbumsState = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
        <BookImage className="h-16 w-16 text-gray-400" strokeWidth={1.5} />
      </div>
      <h2 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
        No Albums Created Yet
      </h2>
      <p className="mb-6 max-w-md text-gray-500 dark:text-gray-400">
        Start organizing your photos by creating your first album. Albums help
        you group related photos together for easy access.
      </p>
      <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
        <div className="flex items-center gap-2">
          <FolderPlus className="h-4 w-4" />
          <span>Click the "Create Album" button to get started.</span>
        </div>
        <div className="flex items-center gap-2">
          <BookImage className="h-4 w-4" />
          <span>Organize your favorite moments into collections.</span>
        </div>
      </div>
    </div>
  );
};
