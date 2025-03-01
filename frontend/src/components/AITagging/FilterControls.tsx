import React, { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';

import { Button } from '../ui/button';
import { MediaItem } from '@/types/Media';
import AITaggingFolderPicker from '../FolderPicker/AITaggingFolderPicker';
import DeleteSelectedImagePage from '../FolderPicker/DeleteSelectedImagePage';
import ErrorDialog from '../Album/Error';
import { Trash2, Filter } from 'lucide-react';

interface FilterControlsProps {
  setFilterTag: (tag: string[]) => void;
  mediaItems: MediaItem[];
  onFolderAdded: (newPaths: string[]) => Promise<void>;
  isLoading: boolean;
  isVisibleSelectedImage: boolean;
  setIsVisibleSelectedImage: (value: boolean) => void;
}

export default function FilterControls({
  setFilterTag,
  mediaItems,
  onFolderAdded,
  isVisibleSelectedImage,
  setIsVisibleSelectedImage,
}: FilterControlsProps) {

  const uniqueTags = React.useMemo(() => {
    const allTags = mediaItems.flatMap((item) => item.tags);
    return Array.from(new Set(allTags))
      .filter((tag): tag is string => typeof tag === 'string')
      .sort();
  }, [mediaItems]);

  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);

  const [selectedFlags, setSelectedFlags] = useState<
    { tag: string; isChecked: boolean }[]
  >([
    { tag: 'All tags', isChecked: false },
    ...uniqueTags.map((ele) => ({ tag: ele, isChecked: false })),
  ]);

  const handleAddFlag = (idx: number) => {
    const updatedFlags = [...selectedFlags];
    updatedFlags[idx].isChecked = true;
    setSelectedFlags(updatedFlags);
  };

  const handleRemoveFlag = (idx: number) => {
    const updatedFlags = [...selectedFlags];
    updatedFlags[idx].isChecked = false;
    setSelectedFlags(updatedFlags);
  };

  const handleFilterFlag = () => {
    let flags: string[] = [];
    if (selectedFlags[0].isChecked) {
      setFilterTag([]);
      return;
    }
    selectedFlags.forEach((ele) => {
      if (ele.isChecked) flags.push(ele.tag);
    });

    console.log('Updated Filter Flags = ', flags);
    setFilterTag(flags);
  };

  const handleToggleDropdown = (event: Event) => {
    event.preventDefault();
    setIsDropdownOpen((prevState) => !prevState); // Toggle dropdown visibility
  };
  const handleFolderPick = async (paths: string[]) => {
    //set addiitional paths here
    try {
      await onFolderAdded(paths);
    } catch (error) {
      console.error('Error adding folder:', error);
    }
  };

  const [errorDialogContent, setErrorDialogContent] = useState<{
    title: string;
    description: string;
  } | null>(null);

  const showErrorDialog = (title: string, err: unknown) => {
    setErrorDialogContent({
      title,
      description:
        err instanceof Error ? err.message : 'An unknown error occurred',
    });
  };

  if (!isVisibleSelectedImage) {
    return (
      <div>
        <DeleteSelectedImagePage
          setIsVisibleSelectedImage={setIsVisibleSelectedImage}
          onError={showErrorDialog}
          uniqueTags={uniqueTags}
          mediaItems={mediaItems}
        />
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center gap-4 overflow-auto">
        <AITaggingFolderPicker setFolderPath={handleFolderPick} />

        <Button
          onClick={() => setIsVisibleSelectedImage(false)}
          variant="outline"
          className="border-gray-500 hover:bg-accent dark:hover:bg-white/10"
        >
          <Trash2 className="h-4 w-4" />
          <p className="ml-1 hidden lg:inline">Delete Images</p>
        </Button>
        <DropdownMenu open={isDropdownOpen} onOpenChange={setIsDropdownOpen}>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              className="flex cursor-default items-center gap-2 border-gray-500 p-2 hover:bg-accent dark:hover:bg-white/10"
              onClick={() => handleToggleDropdown}
            >
              <Filter className="h-4 w-4" />
              Filter by{' '}
              <div className="flex gap-2">
                {selectedFlags.map((ele, idx) =>
                  ele.isChecked ? (
                    <p
                      key={idx}
                      className="flex items-center justify-center gap-1 rounded-lg border-white bg-gray-800 pb-1 pl-2 pr-2 pt-1"
                    >
                      {ele.tag}
                    </p>
                  ) : null,
                )}
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="max-h-[500px] w-[200px] overflow-y-auto"
            align="end"
          >
            <DropdownMenuRadioGroup
              className="overflow-auto"
              onValueChange={handleFilterFlag}
            >
              {selectedFlags.map((ele, index) => (
                <DropdownMenuRadioItem
                  key={ele.tag}
                  value={ele.tag}
                  onSelect={(event) => {
                    selectedFlags[index].isChecked
                      ? handleRemoveFlag(index)
                      : handleAddFlag(index);
                    event.preventDefault();
                  }}
                  className="cursor-pointer"
                >
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer"
                    value={ele.tag}
                    checked={selectedFlags[index].isChecked}
                  />
                  {ele.tag}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>

        <ErrorDialog
          content={errorDialogContent}
          onClose={() => setErrorDialogContent(null)}
        />
      </div>
    </>
  );
}
