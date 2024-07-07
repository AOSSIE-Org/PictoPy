import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LayoutGridIcon, ListOrderedIcon } from "@/components/Icons/Icons";
import { Button } from "@/components/ui/button";

import { SortingControlsProps } from "@/types/video";

export default function SortingControls({
  sortBy,
  setSortBy,
  videosPerRow,
  setVideosPerRow,
}: SortingControlsProps) {
  return (
    <div className="flex items-center gap-4">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <LayoutGridIcon className="w-4 h-4" />
            {videosPerRow} per row
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className="w-[200px] bg-white dark:text-foreground"
          align="end"
        >
          <DropdownMenuRadioGroup
            value={videosPerRow.toString()}
            onValueChange={(value: string) => setVideosPerRow(parseInt(value))}
          >
            <DropdownMenuRadioItem value="2">2 per row</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="3">3 per row</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="4">4 per row</DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <ListOrderedIcon className="w-4 h-4" />
            Sort by {sortBy}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className="w-[200px] bg-white dark:text-foreground"
          align="end"
        >
          <DropdownMenuRadioGroup
            value={sortBy}
            onValueChange={(value: string) =>
              setSortBy(value as "date" | "title" | "popularity")
            }
          >
            <DropdownMenuRadioItem value="date">Date</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="title">Title</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="popularity">
              Popularity
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
