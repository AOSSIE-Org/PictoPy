import { ReactNode } from 'react';

interface MemorySectionProps {
  title: string;
  description?: string;
  children: ReactNode;
  isEmpty?: boolean;
  emptyMessage?: string;
}

export const MemorySection = ({
  title,
  description,
  children,
  isEmpty = false,
  emptyMessage = 'No memories found',
}: MemorySectionProps) => {
  return (
    <div className="mb-8">
      {/* Section Header */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {title}
        </h2>
        {description && (
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            {description}
          </p>
        )}
      </div>

      {/* Section Content */}
      {isEmpty ? (
        <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-8 text-center dark:border-gray-600 dark:bg-gray-800">
          <p className="text-gray-500 dark:text-gray-400">{emptyMessage}</p>
        </div>
      ) : (
        <div className="space-y-4">{children}</div>
      )}
    </div>
  );
};
