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
import { avatars } from '@/constants/avatars';
import { AppFeatures } from '@/components/OnboardingSteps/AppFeatures';
import { RootState } from '@/app/store';

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

  const handleNameChange = (value: string) => {
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
      <Card className="flex max-h-full w-1/2 flex-col gap-3 border p-4">
        <CardHeader className="p-3">
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

        <CardContent className="flex-1 space-y-6 overflow-y-hidden p-1 px-2">
          <div className="mb-5">
            <Label htmlFor="name" className="mb-1 block text-sm">
              Your Name
            </Label>
            <Input
              id="name"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="h-8 text-sm placeholder:text-sm"
            />
          </div>

          {/* Avatar Grid */}
          <div className="mb-5">
            <Label className="mb-2 block text-sm">Choose Your Avatar</Label>
            <div className="grid grid-cols-4 gap-3">
              {avatars.map((avatar) => {
                const isSelected = selectedAvatar === avatar;
                return (
                  <button
                    type="button"
                    key={avatar}
                    onClick={() => handleAvatarSelect(avatar)}
                    className={`bg-background relative inline-flex h-20 w-20 items-center justify-center rounded-full transition-all duration-300 ${
                      isSelected
                        ? 'border-primary ring-primary ring-offset-background ring-2 ring-offset-2'
                        : 'border-muted'
                    }`}
                  >
                    <img
                      src={avatar}
                      alt="Avatar"
                      className={`h-20 w-20 rounded-full object-cover transition-all duration-300 ${
                        isSelected ? 'scale-105' : ''
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex justify-end p-3">
          <Button
            className="cursor-pointer px-4 py-1 text-sm"
            onClick={handleNextClick}
            disabled={!name || !selectedAvatar}
          >
            Next
          </Button>
        </CardFooter>
      </Card>

      <AppFeatures />
    </>
  );
};
