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
import FolderPicker from '../FolderPicker/FolderPicker';
import LoadingScreen from '../ui/LoadingScreen/LoadingScreen';
import DeleteSelectedImagePage from '../FolderPicker/DeleteSelectedImagePage';
import ErrorDialog from '../Album/Error';
import { Trash2, Filter } from 'lucide-react';
import { queryClient, usePictoMutation } from '@/hooks/useQueryExtensio';
import { addFolder } from '../../../api/api-functions/images';

interface FilterControlsProps {
  filterTag: string;
  setFilterTag: (tag: string) => void;
  mediaItems: MediaItem[];
  onFolderAdded: () => Promise<void>;
  isLoading: boolean;
  isVisibleSelectedImage: boolean;
  setIsVisibleSelectedImage: (value: boolean) => void;
}

export default function FilterControls({
  filterTag,
  setFilterTag,
  mediaItems,
  onFolderAdded,
  isLoading,
  isVisibleSelectedImage,
  setIsVisibleSelectedImage,
}: FilterControlsProps) {
  const {
    mutate: addFolderAPI,
    isPending: isAddingFolder,
    errorMessage,
  } = usePictoMutation({
    mutationFn: addFolder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-images'] });
    },
    autoInvalidateTags: ['ai-tagging-images', 'ai'],
  });

  const uniqueTags = React.useMemo(() => {
    const allTags = mediaItems.flatMap((item) => item.tags);
    return Array.from(new Set(allTags))
      .filter((tag): tag is string => typeof tag === 'string')
      .sort();
  }, [mediaItems]);

  const [selectedFlags, setSelectedFlags] = useState<{ tag: string; isChecked: boolean }[]>([
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

  const handleFolderPick = async (path: string) => {
    try {
      addFolderAPI(path);
      await onFolderAdded();
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
      {(isLoading || isAddingFolder) && <LoadingScreen />}
      {errorMessage && errorMessage !== 'Something went wrong' && (
        <div className="text-red-500">Error: {errorMessage}</div>
      )}
      <div className="flex items-center gap-4 overflow-auto">
        <FolderPicker setFolderPath={handleFolderPick} settingsPage={false} />

        <Button
          onClick={() => setIsVisibleSelectedImage(false)}
          variant="outline"
          className="border-gray-500 hover:bg-accent dark:hover:bg-white/10"
        >
          <Trash2 className="h-4 w-4" />
          <p className="ml-1 hidden lg:inline">Delete Images</p>
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              className="flex items-center gap-2 border-gray-500 p-2 hover:bg-accent dark:hover:bg-white/10"
            >
              <Filter className="h-4 w-4" />
              Filter by{' '}
              <div className="flex gap-2">
                {selectedFlags.map((ele, idx) =>
                  ele.isChecked ? (
                    <p
                      key={idx}
                      className="rounded-lg border-white bg-gray-700 pl-2 pr-2"
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
              value={filterTag}
              onValueChange={setFilterTag}
            >
              {selectedFlags.map((ele, index) => (
                <DropdownMenuRadioItem
                  key={ele.tag}
                  value={ele.tag}
                  onSelect={(event) => {
                    event.preventDefault();
                  }}
                >
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer"
                    value={ele.tag}
                    checked={selectedFlags[index].isChecked}
                    onChange={(event) => {
                      event.target.checked
                        ? handleAddFlag(index)
                        : handleRemoveFlag(index);
                    }}
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
