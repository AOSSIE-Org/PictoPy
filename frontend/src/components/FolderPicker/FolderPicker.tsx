import { Button } from '@/components/ui/button';
import { FolderPlus } from 'lucide-react';
import { useFolder } from '@/hooks/useFolder';

export const FolderPicker = () => {
  const { pickSingleFolder, addFolderMutate } = useFolder({
    title: 'Select folders',
  });

  const handlePickFolder = async () => {
    const selectedFolder = await pickSingleFolder();
    if (selectedFolder) {
      addFolderMutate(selectedFolder);
    }
  };

  return (
    <div className="flex w-full gap-3">
      <Button
        onClick={handlePickFolder}
        variant="outline"
        className={`hover:bg-accent flex items-center justify-center border-gray-500 text-gray-700 dark:text-gray-50 dark:hover:bg-white/10`}
      >
        <FolderPlus className="h-[18px] w-[18px]" />
        <p className={`ml-2 inline`}>Add folders</p>
      </Button>
    </div>
  );
};

export default FolderPicker;
