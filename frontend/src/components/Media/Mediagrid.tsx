import { MediaGridProps } from '@/types/Media';
import MediaCard from './MediaCard';

export default function MediaGrid({
  mediaItems,
  openMediaViewer,
  type,
}: MediaGridProps) {
  if (mediaItems.length === 0) {
    return (
      <div className="rounded-2xl flex h-96 flex-col items-center justify-center space-y-4 bg-gradient-to-b from-gray-50/50 to-gray-100/50 shadow-inner dark:from-gray-900/30 dark:to-gray-800/30">
        <div className="rounded-full bg-gray-100 p-6 dark:bg-gray-800/80">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 text-gray-400 dark:text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-600 dark:text-gray-300">
          No media found
        </h1>
        <p className="text-center text-sm text-gray-500 dark:text-gray-400">
          Try adjusting your search filters or uploading new content
        </p>
      </div>
    );
  }

  const getFileName = (path: string) => {
    const fileName = path.split('\\').pop()?.split('/').pop() || path;
    const extension = fileName.split('.').pop();
    const baseName = fileName.replace(`.${extension}`, '');

    if (baseName.length > 15) {
      return `${baseName.slice(0, 15)}...${extension}`;
    }
    return fileName;
  };

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
      {mediaItems.map((item, index) => (
        <div
          key={index}
          onClick={() => openMediaViewer(index)}
          className="group flex transform cursor-pointer flex-col gap-2 transition-all duration-300 hover:-translate-y-1"
        >
          <div className="rounded-xl h-48 overflow-hidden shadow-sm transition-shadow duration-300 group-hover:shadow-xl dark:shadow-gray-900/10 dark:group-hover:shadow-gray-900/20 sm:h-56 md:h-52 lg:h-48 xl:h-44 2xl:h-56">
            <MediaCard item={item} type={type} />
          </div>
          <p className="truncate px-1 text-center text-sm font-medium text-gray-700 transition-colors group-hover:text-blue-600 dark:text-gray-300 dark:group-hover:text-blue-400">
            {getFileName(item.title || '')}
          </p>
        </div>
      ))}
    </div>
  );
}
