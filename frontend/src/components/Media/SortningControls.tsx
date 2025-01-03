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
          className="flex items-center gap-2 border-gray-500"
        >
          <ArrowDownWideNarrow className="h-4 w-4" />
          {`Sort: ${sortingOptions.find((opt) => opt.value === sortBy)?.label || 'Select'}`}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-[200px] dark:bg-background dark:text-foreground"
        align="end"
      >
        <DropdownMenuRadioGroup value={sortBy} onValueChange={handleSortChange}>
          {sortingOptions.map((option) => (
            <DropdownMenuRadioItem key={option.value} value={option.value}>
              {option.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default SortingControls