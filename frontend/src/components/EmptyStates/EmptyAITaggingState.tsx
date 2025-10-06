import { Bot, Tags, Image as ImageIcon } from 'lucide-react';

export const EmptyAITaggingState = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
        <Bot className="h-16 w-16 text-gray-400" />
      </div>
      <h2 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
        No AI Tagged Images
      </h2>
      <p className="mb-6 max-w-md text-gray-500 dark:text-gray-400">
        Your images haven't been processed by AI yet. Add some images to your
        gallery and they will be automatically tagged with AI-powered labels.
      </p>
      <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
        <div className="flex items-center gap-2">
          <Tags className="h-4 w-4" />
          <span>AI will automatically detect objects, people, and scenes</span>
        </div>
        <div className="flex items-center gap-2">
          <ImageIcon className="h-4 w-4" />
          <span>Supports PNG, JPG, JPEG, GIF image formats</span>
        </div>
      </div>
    </div>
  );
};
