import FolderPicker from '@/components/FolderPicker/FolderPicker';
import { PictoPy } from '@/components/ui/Icons/Icons';
import React from 'react';

interface SetupScreenProps {
  onFolderPathsChange: (paths: string[]) => void;
}

export const SetupScreen: React.FC<SetupScreenProps> = ({
  onFolderPathsChange,
}) => (
  <div className="flex min-h-screen items-center justify-center bg-gray-900">
    <div className="animate-fade-in-up flex flex-col items-center justify-center space-y-6">
      <div className="rounded-full flex h-24 w-24 items-center justify-center bg-white">
        <PictoPy className="h-16 w-16 text-gray-900" />
      </div>
      <p className="text-2xl font-bold text-white">PictoPy</p>
      <FolderPicker setFolderPaths={onFolderPathsChange} />
    </div>
  </div>
);
