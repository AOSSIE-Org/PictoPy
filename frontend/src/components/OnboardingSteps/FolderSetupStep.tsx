'use client';

import '@/App.css';
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
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '@/store';
import {
  markCompleted,
  previousStep,
  addFolder,
  removeFolder,
} from '@/features/onboardingSlice';
import React from 'react';
import { AppFeatures } from './AppFeatures';

interface FolderSetupStepProps {
  stepIndex: number;
  totalSteps: number;
}

export function FolderSetupStep({
  stepIndex,
  totalSteps,
}: FolderSetupStepProps) {
  const dispatch = useDispatch<AppDispatch>();
  const folders = useSelector((state: RootState) => state.onboarding.folders);

  const handleSelectFolders = () => {
    const mockFolder = `/home/NewFolder${folders.length + 1}`;
    dispatch(addFolder(mockFolder));
  };

  const handleRemoveFolder = (folder: string) => {
    dispatch(removeFolder(folder));
  };

  const handleNext = () => {
    dispatch(markCompleted(stepIndex));
  };

  const handleBack = () => {
    dispatch(previousStep());
  };

  const progressPercent = Math.round(((stepIndex + 1) / totalSteps) * 100);

  return (
    <div className="bg-muted/10 flex min-h-screen w-full items-center justify-center px-4 py-6">
      <div className="flex h-[85vh] w-full max-w-7xl gap-4">
        {/* Left Card */}
        <Card className="flex max-h-full w-1/2 flex-col border p-4">
          <CardHeader className="border-border border-b p-6 pb-4">
            <div className="text-muted-foreground mb-1 flex justify-between text-xs">
              <span>
                Step {stepIndex + 1} of {totalSteps}
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

          <CardContent className="flex-1 space-y-6 overflow-y-auto p-6">
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

          <CardFooter className="mt-2 flex items-center justify-between px-6 py-3">
            <Button
              variant="outline"
              onClick={handleBack}
              className="px-6 py-3 text-base"
            >
              Back
            </Button>
            <Button onClick={handleNext} className="px-6 py-3 text-base">
              Next
            </Button>
          </CardFooter>
        </Card>

        {/* Right Card */}
        <AppFeatures />
      </div>
    </div>
  );
}
