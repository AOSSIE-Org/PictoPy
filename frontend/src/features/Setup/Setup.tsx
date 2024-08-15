import FolderPicker from "@/components/FolderPicker/FolderPicker";
import { Pitopy } from "@/components/Icons/Icons";
import React from "react";

interface SetupScreenProps {
  onFolderPathChange: (path: string) => void;
}

export const SetupScreen: React.FC<SetupScreenProps> = ({
  onFolderPathChange,
}) => (
  <div className="flex items-center justify-center min-h-screen bg-gray-900">
    <div className="animate-fade-in-up flex flex-col items-center justify-center space-y-6">
      <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center">
        <Pitopy className="w-16 h-16 text-gray-900" />
      </div>
      <p className="text-2xl font-bold text-white">Pictopy</p>
      <FolderPicker setFolderPath={onFolderPathChange} />
    </div>
  </div>
);
