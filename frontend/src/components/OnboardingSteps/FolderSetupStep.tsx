'use client';
import '@/App.css';

import { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FolderPlus, X, Folder } from 'lucide-react';

interface FolderSetupStepProps {
  onNext: () => void;
  onBack: () => void;
  stepIndex: number;
  totalSteps: number;
}

export function FolderSetupStep({
  onNext,
  onBack,
  stepIndex,
  totalSteps,
}: FolderSetupStepProps) {
  const [folders, setFolders] = useState<string[]>([
    '/home/Downloads',
    '/home/Pictures',
  ]);

  const handleSelectFolders = () => {
    const mockFolder = `/home/NewFolder${folders.length + 1}`;
    setFolders((prev) => [...prev, mockFolder]);
  };

  const handleRemoveFolder = (folder: string) => {
    setFolders((prev) => prev.filter((f) => f !== folder));
  };

  const progressPercent = Math.round((stepIndex / totalSteps) * 100);

  return (
    <div className="bg-background text-foreground flex min-h-screen w-full items-start justify-center p-4">
      <div className="border-border bg-card mt-8 mb-8 flex w-full max-w-5xl flex-col rounded-2xl border shadow-xl">
        <CardHeader className="border-border border-b p-6 pb-4">
          <div className="text-muted-foreground mb-1 flex justify-between text-xs">
            <span>
              Step {stepIndex} of {totalSteps}
            </span>
            <span>{progressPercent}%</span>
          </div>
          <div className="bg-muted mb-4 h-2 w-full rounded-full">
            <div
              className="bg-primary h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <CardTitle className="text-2xl font-semibold">
            Select Your Folders
          </CardTitle>
          <CardDescription className="mt-2 text-base">
            Choose the folders you want to import
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 space-y-6 p-6">
          <Button
            variant="default"
            className="w-full py-5 text-base font-medium"
            onClick={handleSelectFolders}
          >
            <FolderPlus className="mr-2 h-5 w-5" />
            Select Folders
          </Button>

          <div className="space-y-4">
            <p className="text-muted-foreground text-sm font-medium">
              Selected Folders
            </p>
            {folders.map((folder, index) => (
              <div
                key={index}
                className="bg-muted flex items-center justify-between rounded-md px-4 py-2 text-sm"
              >
                <div className="flex items-center gap-2">
                  <Folder className="h-4 w-4" />
                  <span>{folder}</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveFolder(folder)}
                  className="text-destructive hover:text-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </CardContent>

        <CardFooter className="border-border flex justify-between border-t p-6 pb-20">
          <Button
            variant="outline"
            onClick={onBack}
            className="mt-2 px-5 py-5 text-sm"
          >
            Back
          </Button>
          <Button onClick={onNext} className="mt-2 px-5 py-5 text-sm">
            Next
          </Button>
        </CardFooter>
      </div>
    </div>
  );
}
