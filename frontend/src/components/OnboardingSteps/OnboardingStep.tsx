import '@/App.css';
import React from 'react';

import { FolderSetupStep } from '@/components/OnboardingSteps/FolderSetupStep';
import { AvatarSelectionStep } from '@/components/OnboardingSteps/AvatarSelectionStep';
import { ThemeSelectionStep } from '@/components/OnboardingSteps/ThemeSelectionStep';
import { STEPS } from '@/constants/steps';
import { UpdateStep } from '@/components/OnboardingSteps/UpdateStep';
import { ServerCheck } from './ServerCheck';

interface OnboardingStepProps {
  stepIndex: number;
  stepName: string;
  currentStepDisplayIndex?: number;
}

const VISIBLE_STEPS = [
  STEPS.AVATAR_SELECTION_STEP,
  STEPS.FOLDER_SETUP_STEP,
  STEPS.THEME_SELECTION_STEP,
];

export const OnboardingStep: React.FC<OnboardingStepProps> = ({
  stepIndex,
  stepName,
  currentStepDisplayIndex,
}) => {
  const STEP_NAMES = Object.values(STEPS);
  const safeIndex = Math.max(0, Math.min(stepIndex, STEP_NAMES.length - 1));
  const currentStepName = stepName || STEP_NAMES[safeIndex];

  const sharedProps = {
    stepIndex: safeIndex,
    totalSteps: VISIBLE_STEPS.length,
    currentStepDisplayIndex,
  };

  const renderStepComponent = () => {
    switch (currentStepName) {
      case STEPS.AVATAR_SELECTION_STEP:
        return <AvatarSelectionStep {...sharedProps} />;
      case STEPS.FOLDER_SETUP_STEP:
        return <FolderSetupStep {...sharedProps} />;
      case STEPS.THEME_SELECTION_STEP:
        return <ThemeSelectionStep {...sharedProps} />;
      case STEPS.UPDATE_STEP:
        return <UpdateStep {...sharedProps} />;
      case STEPS.SERVER_CHECK:
        return <ServerCheck {...sharedProps} />;
      default:
        return <div></div>;
    }
  };

  return (
    <div className="bg-background text-foreground flex min-h-screen w-full items-center justify-center">
      <div className="flex h-[540px] w-full max-w-4xl gap-3">
        {renderStepComponent()}
      </div>
    </div>
  );
};
