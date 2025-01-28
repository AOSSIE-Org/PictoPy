import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  usePictoQuery,
  usePictoMutation,
  queryClient,
} from '@/hooks/useQueryExtensio';
import {
  delMultipleImages,
  fetchAllImages,
} from '../../../api/api-functions/images';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@radix-ui/react-dropdown-menu';
import { Filter } from 'lucide-react';
import { MediaItem } from '@/types/Media';
interface DeleteSelectedImageProps {
  setIsVisibleSelectedImage: (value: boolean) => void;
  onError: (title: string, err: any) => void;
  uniqueTags: string[];
  mediaItems: MediaItem[];
}

const DeleteSelectedImagePage: React.FC<DeleteSelectedImageProps> = ({
  setIsVisibleSelectedImage,
  onError,
  uniqueTags,
  mediaItems
}) => {
  const [selectedImages, setSelectedImages] = useState<string[]>([]);

  const { successData: response, isLoading } = usePictoQuery({
    queryFn: fetchAllImages,
    queryKey: ['all-images'],
  });

  
  const { mutate: deleteMultipleImages, isPending: isAddingImages } =
  usePictoMutation({
    mutationFn: delMultipleImages,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-images'] });
    },
    autoInvalidateTags: ['ai-tagging-images', 'ai'],
  });
  
  // Extract the array of image paths
  const allImages: string[] = response?.image_files || [];
  const toggleImageSelection = (imagePath: string) => {
    setSelectedImages((prev) =>
      prev.includes(imagePath)
        ? prev.filter((path) => path !== imagePath)
        : [...prev, imagePath],
    );
  };

  const handleAddSelectedImages = async () => {
    if (selectedImages.length > 0) {
      try {
        await deleteMultipleImages(selectedImages);
        console.log('Selected Images : ', selectedImages);
        setSelectedImages([]);
        if (!isLoading) {
          setIsVisibleSelectedImage(true);
        }
      } catch (err) {
        onError('Error during deleting images', err);
      }
    }
  };


  const [filterTag, setFilterTag] = useState<string>(uniqueTags[0]);

  const handleFilterTag = (value: string) => {
    setSelectedImages([]); 
    setFilterTag(value); 
    
    if(value.length === 0) {
      setSelectedImages(allImages);
      return;
    }

    const selectedImagesPaths: string[] = [];
    
    mediaItems.forEach((ele) => {
      if (ele.tags?.includes(value)) {
        ele.imagePath && selectedImagesPaths.push(ele.imagePath);
      }
    });
  
    console.log("Selected Images Path = ", selectedImagesPaths);
    setSelectedImages(selectedImagesPaths);
  };
  




  const getImageName = (path: string) => {
    return path.split('\\').pop() || path;
  };

  if (isLoading) {
    return <div>Loading images...</div>;
  }

  if (!Array.isArray(allImages) || allImages.length === 0) {
    return <div>No images available. Please add some images first.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center justify-between">
        <h1 className="mb-4 text-2xl font-bold">Select Images</h1>
        <div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="flex items-center gap-2 rounded-lg border-gray-500 px-4 py-2 shadow-sm transition duration-300 ease-in-out hover:bg-accent dark:hover:bg-white/10"
              >
                <Filter className="h-4 w-4 text-gray-700 dark:text-white" />
                <p className="hidden text-sm text-gray-700 dark:text-white lg:inline">
                  Select Tag :  {filterTag || 'tags'}
                </p>
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent
              className="z-50 max-h-[500px] w-[200px] overflow-y-auto rounded-lg bg-gray-800 p-2 shadow-lg dark:bg-gray-900"
              align="end"
            >
              <DropdownMenuRadioGroup
                className="overflow-auto rounded-lg bg-gray-950 text-white"
                value={filterTag}
                onValueChange={(value)=>handleFilterTag(value)}
              >
                <DropdownMenuRadioItem
                  value=""
                  className="rounded-md px-4 py-2 text-sm transition-colors duration-200 hover:bg-gray-700 hover:text-white"
                >
                  All tags
                </DropdownMenuRadioItem>
                {uniqueTags.map((tag) => (
                  <DropdownMenuRadioItem
                    key={tag}
                    value={tag}
                    className="rounded-md px-4 py-2 text-sm transition-colors duration-200 hover:bg-gray-700 hover:text-white"
                  >
                    {tag}
                  </DropdownMenuRadioItem>
                ))}
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        {/* <button onClick={handleSelectAllImages}>Select All</button> */}
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {mediaItems.map(({ imagePath, thumbnailUrl }, index) => {
          return (
            <div key={index} className="relative">
              <div
                className={`rounded-full absolute -right-2 -top-2 z-10 h-6 w-6 cursor-pointer border-2 border-white ${
                  imagePath && selectedImages.includes(imagePath)
                    ? 'bg-blue-500'
                    : 'bg-gray-300'
                }`}
                onClick={() => imagePath && toggleImageSelection(imagePath)}
              />
              <img
                src={thumbnailUrl}
                alt={`Image ${ imagePath && getImageName(imagePath)}`}
                className="h-40 w-full rounded-lg object-cover"
              />
              <div className="absolute bottom-0 left-0 right-0 truncate rounded-b-lg bg-black bg-opacity-50 p-1 text-xs text-white">
                {imagePath && getImageName(imagePath)}
              </div>
            </div>
          );
        })}
      </div>
      <div className="fixed bottom-0 left-0 right-0 z-50 mb-4 flex justify-evenly bg-transparent p-4 shadow-lg">
        <Button
          variant="secondary"
          onClick={() => setIsVisibleSelectedImage(true)}
        >
          Cancel
        </Button>
        <Button
          onClick={handleAddSelectedImages}
          variant="destructive"
          disabled={isAddingImages || selectedImages.length === 0}
        >
          Delete Selected Images ({selectedImages.length})
        </Button>
      </div>
    </div>
  );
};

export default DeleteSelectedImagePage;
