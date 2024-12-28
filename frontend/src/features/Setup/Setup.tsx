import FolderPicker from '@/components/FolderPicker/FolderPicker';
import { Pitopy } from '@/components/ui/Icons/Icons';
import React from 'react';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
interface SetupScreenProps {
  onFolderPathChange: (path: string) => void;
}

export const SetupScreen: React.FC<SetupScreenProps> = ({
  onFolderPathChange,
}) => {
  const [loading, setLoading] = React.useState(true);
  if (loading) {
    return <LoadingScreen />;
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900">
      <div className="animate-fade-in-up flex flex-col items-center justify-center space-y-6">
        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-white">
          <Pitopy className="h-16 w-16 text-gray-900" />
        </div>
        <p className="text-2xl font-bold text-white">PictoPy</p>
        <FolderPicker
          setFolderPath={onFolderPathChange}
          AITaggingPage={false}
          setIsLoading={setLoading}
        />
      </div>
    </div>
  );
};
