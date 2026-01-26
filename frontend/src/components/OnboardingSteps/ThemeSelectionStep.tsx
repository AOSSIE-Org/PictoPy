import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '@/app/store';
import { markCompleted, previousStep } from '@/features/onboardingSlice';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  CardDescription,
} from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Sun, Moon, Monitor } from 'lucide-react';

import { AppFeatures } from '@/components/OnboardingSteps/AppFeatures';
import { useTheme } from '@/contexts/ThemeContext';

import { setIsEditing } from '@/features/onboardingSlice';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
interface ThemeSelectionStepProps {
  stepIndex: number;
  totalSteps: number;
  currentStepDisplayIndex: number;
}

export const ThemeSelectionStep: React.FC<ThemeSelectionStepProps> = ({
  stepIndex,
  totalSteps,
  currentStepDisplayIndex,
}) => {
  const { setTheme, theme } = useTheme();
  const isEditing = useSelector(
    (state: RootState) => state.onboarding.isEditing,
  );
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    if (localStorage.getItem('themeChosen') === 'true' && !isEditing) {
      dispatch(markCompleted(stepIndex));
    }
  }, []);
  const handleThemeChange = (value: 'light' | 'dark' | 'system') => {
    setTheme(value);
  };

  const handleNext = () => {
    localStorage.setItem('themeChosen', 'true');
    dispatch(markCompleted(stepIndex));
  };

  const handleBack = () => {
    dispatch(setIsEditing(true));
    dispatch(previousStep());
  };
  if (localStorage.getItem('themeChosen') === 'true' && !isEditing) {
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
            Choose Your Theme
          </CardTitle>
          <CardDescription className="mt-2 text-base">
            Choose your preferred appearance
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 space-y-6 overflow-y-auto p-1 px-2">
          <RadioGroup
            value={theme}
            onValueChange={handleThemeChange}
            className="space-y-4"
          >
            <Label
              htmlFor="light"
              className="hover:bg-muted/50 flex cursor-pointer items-center space-x-4 rounded-lg border p-4 transition-colors"
            >
              <RadioGroupItem value="light" id="light" />
              <div className="flex items-center space-x-3">
                <Sun className="text-primary h-5 w-5" />
                <span className="text-base font-medium">Light Mode</span>
              </div>
            </Label>

            <Label
              htmlFor="dark"
              className="hover:bg-muted/50 flex cursor-pointer items-center space-x-4 rounded-lg border p-4 transition-colors"
            >
              <RadioGroupItem value="dark" id="dark" />
              <div className="flex items-center space-x-3">
                <Moon className="text-primary h-5 w-5" />
                <span className="text-base font-medium">Dark Mode</span>
              </div>
            </Label>

            <Label
              htmlFor="system"
              className="hover:bg-muted/50 flex cursor-pointer items-center space-x-4 rounded-lg border p-4 transition-colors"
            >
              <RadioGroupItem value="system" id="system" />
              <div className="flex items-center space-x-3">
                <Monitor className="text-primary h-5 w-5" />
                <span className="text-base font-medium">System Default</span>
              </div>
            </Label>
          </RadioGroup>
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
};
