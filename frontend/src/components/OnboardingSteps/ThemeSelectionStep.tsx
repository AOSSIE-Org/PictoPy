'use client';

import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store';
import {
  setTheme,
  markCompleted,
  previousStep,
} from '@/features/onboardingSlice';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';

interface ThemeSelectionStepProps {
  stepIndex: number;
  totalSteps: number;
}

const features = [
  {
    title: 'Smart Tagging',
    description:
      'Automatically tag photos based on detected objects and faces.',
    icon: '🏷️',
  },
  {
    title: 'Album Management',
    description: 'Easily organize your photos into albums with AI suggestions.',
    icon: '📁',
  },
  {
    title: 'Advanced Image Analysis',
    description: 'Analyze image content for smarter organization and search.',
    icon: '🧠',
  },
  {
    title: 'Privacy & Offline Access',
    description: 'Your data stays with you. Full offline access and privacy.',
    icon: '🔒',
  },
];

export const ThemeSelectionStep: React.FC<ThemeSelectionStepProps> = ({
  stepIndex,
  totalSteps,
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const selectedTheme = useSelector(
    (state: RootState) => state.onboarding.theme,
  );
  const [featureIndex, setFeatureIndex] = useState(0);

  useEffect(() => {
    const stored = localStorage.getItem('theme') || 'system';
    dispatch(setTheme(stored));

    if (stored === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute(
        'data-theme',
        isDark ? 'dark' : 'light',
      );
    } else {
      document.documentElement.setAttribute('data-theme', stored);
    }
  }, [dispatch]);

  useEffect(() => {
    if (selectedTheme === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute(
        'data-theme',
        isDark ? 'dark' : 'light',
      );
    } else if (selectedTheme) {
      document.documentElement.setAttribute('data-theme', selectedTheme);
    }
    if (selectedTheme) {
      localStorage.setItem('theme', selectedTheme);
    }
  }, [selectedTheme]);

  useEffect(() => {
    const interval = setInterval(() => {
      setFeatureIndex((prev) => (prev + 1) % features.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const currentFeature = features[featureIndex];

  const handleThemeChange = (value: string) => {
    dispatch(setTheme(value));
  };

  const handleNext = () => {
    dispatch(markCompleted(stepIndex));
  };

  const handleBack = () => {
    dispatch(previousStep());
  };

  return (
    <div className="flex h-screen w-full items-center justify-start pr-4 pl-6">
      <div className="flex h-[75vh] w-full max-w-7xl gap-3">
        {/* Left Card */}
        <Card className="flex basis-1/2 flex-col overflow-hidden border p-2">
          <CardHeader className="mt-2 pb-2">
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

          <CardTitle className="mb-1 ml-4 text-lg font-semibold">
            Choose Your Theme
          </CardTitle>
          <p className="text-muted-foreground mb-4 ml-4 text-sm">
            Select your preferred appearance
          </p>

          <CardContent className="flex-1 space-y-8 text-[16px]">
            <RadioGroup
              value={selectedTheme}
              onValueChange={handleThemeChange}
              className="space-y-8"
            >
              <div className="ml-4 flex items-center space-x-2">
                <RadioGroupItem value="light" id="light" />
                <Label htmlFor="light">🌞 Light Mode</Label>
              </div>
              <div className="ml-4 flex items-center space-x-2">
                <RadioGroupItem value="dark" id="dark" />
                <Label htmlFor="dark">🌙 Dark Mode</Label>
              </div>
              <div className="ml-4 flex items-center space-x-2">
                <RadioGroupItem value="system" id="system" />
                <Label htmlFor="system">🖥️ System Default</Label>
              </div>
            </RadioGroup>
          </CardContent>

          <CardFooter className="mt-auto mb-4 flex justify-between px-4">
            <Button
              variant="outline"
              onClick={handleBack}
              className="px-5 py-2 text-sm"
            >
              Back
            </Button>
            <Button onClick={handleNext} className="px-5 py-2 text-sm">
              Next
            </Button>
          </CardFooter>
        </Card>

        {/* Right Card */}
        <Card className="flex basis-1/2 flex-col items-center justify-center overflow-hidden border p-2 text-center">
          <div className="flex flex-col items-center justify-center">
            <div className="mb-3 text-5xl">{currentFeature.icon}</div>{' '}
            {/* Increased from text-4xl */}
            <h2 className="mb-2 text-lg font-semibold">
              {currentFeature.title}
            </h2>{' '}
            {/* text-base -> text-lg */}
            <p className="text-muted-foreground mb-4 text-sm">
              {currentFeature.description}
            </p>
            <div className="flex justify-center gap-1">
              {features.map((_, index) => (
                <div
                  key={index}
                  className={`h-2 w-2 rounded-full ${
                    index === featureIndex
                      ? 'bg-foreground'
                      : 'bg-muted-foreground/40'
                  }`}
                />
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
