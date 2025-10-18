import { Search } from 'lucide-react';

export const EmptySearchState = () => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
      <Search className="h-16 w-16 text-gray-400" />
    </div>
    <h2 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
      No Search Results
    </h2>
    <p className="mb-6 max-w-md text-gray-500 dark:text-gray-400">
      No images match your search criteria. Try adjusting your search or try a
      different face image.
    </p>
    <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
      <div className="flex items-center gap-2">
        <Search className="h-4 w-4" />
        <span>Try adjusting the face image selection</span>
      </div>
      <div className="flex items-center gap-2">
        <Search className="h-4 w-4" />
        <span>
          Make sure the face is clearly visible in the reference image
        </span>
      </div>
    </div>
  </div>
);
