'use client';

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store';
import {
  setAvatar,
  setName,
  markCompleted,
} from '../../features/onboardingSlice';

import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import { AppFeatures } from './AppFeatures';

interface AvatarNameSelectionStepProps {
  stepIndex: number;
  totalSteps: number;
}

const avatars = [
  '/avatars/avatar1.png',
  '/avatars/avatar2.png',
  '/avatars/avatar3.png',
  '/avatars/avatar4.png',
  '/avatars/avatar5.png',
  '/avatars/avatar6.png',
  '/avatars/avatar7.png',
  '/avatars/avatar8.png',
];

export const AvatarSelectionStep: React.FC<AvatarNameSelectionStepProps> = ({
  stepIndex,
  totalSteps,
}) => {
  const dispatch = useDispatch();
  const name = useSelector((state: RootState) => state.onboarding.name);
  const selectedAvatar = useSelector(
    (state: RootState) => state.onboarding.avatar,
  );

  const handleAvatarSelect = (avatar: string) => {
    dispatch(setAvatar(avatar));
  };

  const handleNameChange = (value: string) => {
    dispatch(setName(value));
  };

  const handleNextClick = () => {
    if (name && selectedAvatar) {
      dispatch(markCompleted(stepIndex));
    } else {
      alert('Please enter your name and select an avatar.');
    }
  };

  return (
    <div className="bg-background text-foreground flex h-screen w-full items-center justify-center">
      <div className="flex h-[75vh] w-full max-w-7xl gap-3">
        {/* Left Card */}
        <Card className="flex basis-1/2 flex-col overflow-hidden border p-0">
          <div className="flex h-full flex-col overflow-auto px-6 py-4">
            <CardHeader className="mt-2 px-0 pb-2">
              <div className="text-muted-foreground mb-1 flex justify-between text-xs">
                <span>
                  Step {stepIndex + 1} of {totalSteps}
                </span>
                <span>{Math.round(((stepIndex + 1) / totalSteps) * 100)}%</span>
              </div>
              <div className="bg-muted mb-2 h-1.5 w-full rounded-full">
                <div
                  className="bg-primary h-full rounded-full transition-all duration-300"
                  style={{ width: `${((stepIndex + 1) / totalSteps) * 100}%` }}
                />
              </div>
            </CardHeader>

            <h2 className="mb-1 text-lg font-semibold">Welcome to PictoPy</h2>
            <p className="text-muted-foreground mb-4 text-sm">
              Let's get to know you a little better
            </p>

            {/* Name Input */}
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

            {/* Next Button */}
            <div className="mt-auto flex justify-end pt-4">
              <Button className="px-4 py-1 text-sm" onClick={handleNextClick}>
                Next
              </Button>
            </div>
          </div>
        </Card>

        {/* Right Card using AppFeatures */}
        <AppFeatures />
      </div>
    </div>
  );
};
