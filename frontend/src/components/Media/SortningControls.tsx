import React from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { SortingControlsProps } from '@/types/Media';
import { ArrowDownWideNarrow } from 'lucide-react';

const SortingControls: React.FC<SortingControlsProps> = ({
  sortBy,
  setSortBy,
  mediaItems,
}) => {
  const handleSortChange = (value: string) => {
    setSortBy(value);
  };

  // Extract years from image data
  const years = mediaItems.reduce<string[]>((acc, curr) => {
    if (curr.date) {
      const year = new Date(curr.date).getFullYear().toString();
      if (!acc.includes(year)) acc.push(year);
    }
    return acc;
  }, []);

  years.sort((a, b) => parseInt(b) - parseInt(a));

  const sortingOptions = [
    { value: 'date', label: 'Sort by Date' },
    { value: 'name', label: 'Sort by Name (A-Z)' },
    { value: 'desc', label: 'Sort by Name (Z-A)' },
    { value: 'size', label: 'Sort by Size' },
    { value: 'type', label: 'Sort by Type' },
    { value: 'favorites', label: 'Sort by Favorites' },
    ...years.map((year) => ({
      value: `year-${year}`,
      label: `Sort by Year (${year})`,
    })),
  ];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="flex items-center gap-2.5 border border-gray-200/80 bg-white/90 px-4 py-2.5 text-sm font-medium shadow-sm backdrop-blur transition-all duration-200 hover:bg-gray-50/90 hover:shadow-md dark:border-gray-800/80 dark:bg-gray-800/80 dark:text-gray-100 dark:hover:bg-gray-700/90 dark:hover:text-white"
        >
          <ArrowDownWideNarrow className="mt-[1px] h-4 w-4 text-gray-500 dark:text-gray-400" />
          <span className="max-w-[180px] truncate">
            {sortingOptions.find((opt) => opt.value === sortBy)?.label ||
              'Select'}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-[240px] rounded-xl border border-gray-200/80 bg-white/95 p-1.5 shadow-lg backdrop-blur-sm transition-all dark:border-gray-800/80 dark:bg-gray-800/95 dark:text-gray-100"
        align="end"
        sideOffset={5}
      >
        <DropdownMenuRadioGroup value={sortBy} onValueChange={handleSortChange}>
          {sortingOptions.map((option) => (
            <DropdownMenuRadioItem
              key={option.value}
              value={option.value}
              className="cursor-pointer rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors hover:bg-gray-100/80 dark:hover:bg-gray-700/80"
            >
              {option.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default SortingControls;
