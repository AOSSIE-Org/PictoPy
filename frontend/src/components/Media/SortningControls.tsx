import React from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

import { Button } from '@/components/ui/button';
import { SortingControlsProps, YearOption } from '@/types/Media';
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
      if (!acc.includes(year)) {
        acc.push(year);
      }
    }
    return acc;
  }, []);

  // Sort years in descending order
  years.sort((a, b) => parseInt(b) - parseInt(a));

  // Generate year options for dropdown
  const yearOptions: YearOption[] = years.map((year) => ({
    value: `year-${year}`,
    label: year,
  }));
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="flex items-center gap-2">
          <ArrowDownWideNarrow className="h-4 w-4" />
          <p className="pb-[1px]">Sort by {sortBy}</p>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-[200px] bg-white dark:text-foreground"
        align="end"
      >
        <DropdownMenuRadioGroup value={sortBy} onValueChange={handleSortChange}>
          <DropdownMenuRadioItem value="date">Date</DropdownMenuRadioItem>
          {yearOptions.map((option) => (
            <DropdownMenuRadioItem key={option.value} value={option.value}>
              {option.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default SortingControls;
