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
import { FolderOpen, X, Folder } from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/app/store';
import { markCompleted, previousStep } from '@/features/onboardingSlice';
import { AppFeatures } from '@/components/OnboardingSteps/AppFeatures';
import { useFolder } from '@/hooks/useFolder';
import { useEffect, useState } from 'react';
import { setIsEditing } from '@/features/onboardingSlice';
interface FolderSetupStepProps {
  stepIndex: number;
  totalSteps: number;
  currentStepDisplayIndex: number;
}

export function FolderSetupStep({
  stepIndex,
  totalSteps,
  currentStepDisplayIndex,
}: FolderSetupStepProps) {
  const dispatch = useDispatch<AppDispatch>();

  // Local state for folders
  const [folder, setFolder] = useState<string>('');
  const isEditing = useSelector(
    (state: RootState) => state.onboarding.isEditing,
  );

  useEffect(() => {
    if (localStorage.getItem('folderChosen') === 'true' && !isEditing) {
      dispatch(markCompleted(stepIndex));
    }
  }, []);

  const { pickSingleFolder, addFolderMutate } = useFolder({
    title: 'Select folder to import photos from',
  });

  const handleSelectFolders = async () => {
    const selectedFolder = await pickSingleFolder();
    if (selectedFolder) {
      setFolder(selectedFolder);
    }
  };

  const handleRemoveFolder = () => {
    setFolder('');
  };

  const handleNext = () => {
    localStorage.setItem('folderChosen', 'true');
    addFolderMutate(folder);
    dispatch(markCompleted(stepIndex));
  };

  const handleBack = () => {
    dispatch(setIsEditing(true));
    dispatch(previousStep());
  };

  if (localStorage.getItem('folderChosen') === 'true' && !isEditing) {
    return null;
  }
  const progressPercent = Math.round(
    ((currentStepDisplayIndex + 1) / totalSteps) * 100,
  );

  return (
    <>
      <Card className="flex max-h-full w-1/2 flex-col border p-4">
        <CardHeader className="p-3">
          <div className="text-muted-foreground mb-1 flex justify-between text-xs">
            <span>
              Step {currentStepDisplayIndex + 1} of {totalSteps}
            </span>
            <span>{progressPercent}%</span>
          </div>
          <div className="bg-muted mb-4 h-2 w-full rounded-full">
            <div
              className="bg-primary h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <CardTitle className="text-xl font-semibold">
            Select Your First Folder
          </CardTitle>
          <CardDescription className="mt-2 text-base">
            Choose the folder you want to import your photos from
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 space-y-6 overflow-y-auto p-1 px-2">
          {!folder && (
            <div
              onClick={handleSelectFolders}
              className="border-muted-foreground hover:border-primary hover:bg-muted/50 flex h-[90%] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors"
            >
              <FolderOpen
                className="text-muted-foreground mb-3 h-12 w-12"
                strokeWidth={1}
              />
              <p className="text-muted-foreground text-center text-base font-medium">
                Click to select a folder
              </p>
            </div>
          )}

          {folder && (
            <div className="space-y-4">
              <div className="bg-card hover:border-primary/20 group relative flex items-center justify-between rounded-lg border px-4 py-3 transition-all duration-200">
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <div className="bg-primary/10 text-primary flex h-8 w-8 items-center justify-center rounded-md">
                    <Folder className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {folder.split('/').pop()}
                    </p>
                    <p className="text-muted-foreground truncate text-xs">
                      {folder}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveFolder()}
                  className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 ml-2 flex h-7 w-7 items-center justify-center rounded-md opacity-0 transition-colors group-hover:opacity-100"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex justify-between p-3">
          <Button
            variant="outline"
            onClick={handleBack}
            className="cursor-pointer px-4 py-1 text-sm"
          >
            Back
          </Button>
          <Button
            onClick={handleNext}
            className="cursor-pointer px-4 py-1 text-sm"
          >
            Next
          </Button>
        </CardFooter>
      </Card>

      <AppFeatures />
    </>
  );
}
