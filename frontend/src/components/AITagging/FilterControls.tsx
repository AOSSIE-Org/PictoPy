import React from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";

import { Button } from "../ui/button";
import { MediaItem } from "@/types/Media";
import FolderPicker from "../FolderPicker/FolderPicker";
import { useAddFolder } from "@/hooks/AI_Image";
import LoadingScreen from "../ui/LoadingScreen/LoadingScreen";
import { ListOrderedIcon } from "../ui/Icons/Icons";

interface FilterControlsProps {
  filterTag: string;
  setFilterTag: (tag: string) => void;
  mediaItems: MediaItem[];
  onFolderAdded: () => Promise<void>;
  isLoading: boolean;
}

export default function FilterControls({
  filterTag,
  setFilterTag,
  mediaItems,
  onFolderAdded,
  isLoading,
}: FilterControlsProps) {
  const {
    addFolder,
    isLoading: isAddingFolder,
    error: addFolderError,
  } = useAddFolder();

  const uniqueTags = React.useMemo(() => {
    const allTags = mediaItems.flatMap((item) => item.tags);
    return Array.from(new Set(allTags))
      .filter((tag): tag is string => typeof tag === "string")
      .sort();
  }, [mediaItems]);

  const handleFolderPick = async (path: string) => {
    try {
      await addFolder(path);
      await onFolderAdded();
    } catch (error) {
      console.error("Error adding folder:", error);
    }
  };

  return (
    <>
      {(isLoading || isAddingFolder) && <LoadingScreen />}
      {addFolderError && (
        <div className="text-red-500">Error: {addFolderError}</div>
      )}
      <div className="flex items-center gap-4 overflow-auto">
        <FolderPicker setFolderPath={handleFolderPick} />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="flex items-center gap-2">
              <ListOrderedIcon className="w-4 h-4" />
              Filter by {filterTag || "tags"}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[200px] bg-white  dark:text-foreground"
            align="end"
          >
            <DropdownMenuRadioGroup
              className="overflow-auto"
              value={filterTag}
              onValueChange={setFilterTag}
            >
              <DropdownMenuRadioItem value="">All tags</DropdownMenuRadioItem>
              {uniqueTags.map((tag) => (
                <DropdownMenuRadioItem key={tag} value={tag}>
                  {tag}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </>
  );
}
