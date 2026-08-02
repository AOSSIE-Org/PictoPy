import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  setAvatar,
  setName,
  markCompleted,
} from '../../features/onboardingSlice';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardHeader,
  CardContent,
  CardDescription,
  CardTitle,
  CardFooter,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Pencil } from 'lucide-react';
import { avatars } from '@/constants/avatars';
import { AppFeatures } from '@/components/OnboardingSteps/AppFeatures';
import { RootState } from '@/app/store';
import { AvatarCropDialog } from '@/components/Dialog/avatarCropDialog';
import { pickImageFile } from '@/utils/PFPutils/pickImagePFP';
import { showGlobalAlert } from '@/features/globalAlertSlice';

interface AvatarNameSelectionStepProps {
  stepIndex: number;
  totalSteps: number;
  currentStepDisplayIndex: number;
}

export const AvatarSelectionStep: React.FC<AvatarNameSelectionStepProps> = ({
  stepIndex,
  totalSteps,
  currentStepDisplayIndex,
}) => {
  const dispatch = useDispatch();

  const [name, setLocalName] = useState(localStorage.getItem('name') || '');
  const [selectedAvatar, setLocalAvatar] = useState(
    localStorage.getItem('avatar') || '',
  );
  const isEditing = useSelector(
    (state: RootState) => state.onboarding.isEditing,
  );
  const [longWordError, setLongWordError] = useState(false);
  const [rawImage, setRawImage] = useState<string | null>(null);
  const [cropDialogOpen, setCropDialogOpen] = useState(false);

  useEffect(() => {
    if (
      localStorage.getItem('name') &&
      localStorage.getItem('avatar') &&
      !isEditing
    ) {
      dispatch(markCompleted(stepIndex));
    }
  }, []);

  const handleAvatarSelect = (avatar: string) => {
    setLocalAvatar(avatar);
  };

  const handleUploadClick = async () => {
    try {
      const dataUrl = await pickImageFile();
      if (!dataUrl) return;
      setRawImage(dataUrl);
      setCropDialogOpen(true);
    } catch (error) {
      console.error('Failed to read selected image:', error);
      dispatch(
        showGlobalAlert({
          title: 'Upload failed',
          message: 'Could not read the selected image. Please try again.',
        }),
      );
    }
  };

  const handleCropped = (dataUrl: string) => {
    setLocalAvatar(dataUrl);
    setRawImage(null);
  };

  const handleNameChange = (value: string) => {
    const words = value.split(' ');
    const hasLongWord = words.some((word) => word.length > 30);
    if (hasLongWord) {
      setLongWordError(true);
      return;
    }
    setLongWordError(false);
    setLocalName(value);
  };

  const handleNextClick = () => {
    dispatch(setName(name));
    dispatch(setAvatar(selectedAvatar));
    localStorage.setItem('name', name);
    localStorage.setItem('avatar', selectedAvatar);
    dispatch(markCompleted(stepIndex));
  };

  if (
    localStorage.getItem('name') &&
    localStorage.getItem('avatar') &&
    !isEditing
  ) {
    return null;
  }

  return (
    <>
      <Card className="flex max-h-full w-1/2 flex-col gap-3 border p-6">
        <CardHeader className="px-0 pt-1 pb-1!">
          <div className="text-muted-foreground mb-1 flex justify-between text-xs">
            <span>
              Step {currentStepDisplayIndex + 1} of {totalSteps}
            </span>
            <span>
              {Math.round(((currentStepDisplayIndex + 1) / totalSteps) * 100)}%
            </span>
          </div>
          <div className="bg-muted mb-2 h-1.5 w-full rounded-full">
            <div
              className="bg-primary h-full rounded-full transition-all duration-300"
              style={{
                width: `${((currentStepDisplayIndex + 1) / totalSteps) * 100}%`,
              }}
            />
          </div>
          <CardTitle className="mt-1 text-xl font-semibold">
            Welcome to PictoPy
          </CardTitle>
          <CardDescription className="mt-1 text-base">
            Let's get to know you a little better
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 space-y-5 overflow-y-auto p-1 px-2">
          {/* Avatar + Name row */}
          <div className="flex items-end gap-3 rounded-lg border bg-neutral-900 p-3">
            <button
              type="button"
              onClick={handleUploadClick}
              aria-label="Change profile avatar"
              className="group relative inline-flex h-14 w-14 shrink-0 items-center justify-center rounded-full"
            >
              {selectedAvatar ? (
                <img
                  src={selectedAvatar}
                  alt="Current avatar"
                  className="h-14 w-14 rounded-full object-cover ring-2 ring-blue-500"
                />
              ) : (
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-neutral-800 ring-2 ring-blue-500">
                  <span className="text-[9px] font-medium tracking-wide text-neutral-500 uppercase select-none">
                    Preview
                  </span>
                </div>
              )}
              <span className="border-background absolute right-0 bottom-0 flex h-5 w-5 items-center justify-center rounded-full border-2 bg-blue-500 text-white transition-transform group-hover:scale-105">
                <Pencil className="h-3 w-3" aria-hidden="true" />
              </span>
            </button>

            <div className="min-w-0 flex-1">
              <Label
                htmlFor="name"
                className="mb-1 block text-xs font-medium tracking-wide text-neutral-500"
              >
                Your Name
              </Label>
              <Input
                id="name"
                placeholder="Enter your name"
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                className="placeholder:text-md h-11 border-0 bg-transparent py-0 pr-0 pl-2 text-lg font-normal tracking-tight shadow-none placeholder:font-normal placeholder:tracking-normal placeholder:text-neutral-500 focus-visible:ring-0"
              />
              {longWordError && (
                <p className="mt-1.5 text-xs text-red-500">
                  A single word cannot exceed 30 characters.
                </p>
              )}
            </div>
          </div>

          {/* Avatar Grid */}
          <div>
            <div className="mb-3 pl-2">
              <Label className="text-sm">Choose Your Avatar</Label>
            </div>
            <div className="flex flex-wrap justify-center gap-x-6 gap-y-3">
              {avatars.map((avatar) => {
                const isSelected = selectedAvatar === avatar;
                return (
                  <button
                    type="button"
                    key={avatar}
                    onClick={() => handleAvatarSelect(avatar)}
                    className={`bg-background relative inline-flex h-15 w-15 items-center justify-center rounded-full transition-all duration-300 ${
                      isSelected
                        ? 'border-primary ring-primary ring-offset-background ring-2 ring-offset-2'
                        : 'border-muted'
                    }`}
                  >
                    <img
                      src={avatar}
                      alt="Avatar"
                      className={`h-15 w-15 rounded-full object-cover transition-all duration-300 ${
                        isSelected ? 'scale-105' : ''
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex justify-end p-1">
          <Button
            className="cursor-pointer px-4 py-1 text-sm"
            onClick={handleNextClick}
            disabled={!name || !selectedAvatar || longWordError}
          >
            Next
          </Button>
        </CardFooter>
      </Card>

      <AppFeatures />

      <AvatarCropDialog
        open={cropDialogOpen}
        onOpenChange={setCropDialogOpen}
        imageSrc={rawImage}
        onCropped={handleCropped}
      />
    </>
  );
};
