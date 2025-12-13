import { Sparkles, Calendar, MapPin } from 'lucide-react';

export const EmptyMemoriesState = () => {
  return (
    <div className="flex h-full flex-col items-center justify-center py-16 text-center">
      <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
        <Sparkles className="h-16 w-16 text-gray-400" strokeWidth={1.5} />
      </div>
      <h2 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
        No Memories Yet
      </h2>
      <p className="mb-6 max-w-md text-gray-500 dark:text-gray-400">
        Memories are automatically generated from your photos based on time and
        location. Add more photos to your gallery to see memories appear here.
      </p>
      <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
        <div className="flex items-center justify-center gap-2">
          <Calendar className="h-4 w-4" />
          <span>Memories are grouped by date and time</span>
        </div>
        <div className="flex items-center justify-center gap-2">
          <MapPin className="h-4 w-4" />
          <span>Photos with location data create trip memories</span>
        </div>
        <div className="flex items-center justify-center gap-2">
          <Sparkles className="h-4 w-4" />
          <span>Special moments are highlighted automatically</span>
        </div>
      </div>
    </div>
  );
};
