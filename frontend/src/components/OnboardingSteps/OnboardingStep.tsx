import '@/App.css';
import React from 'react';

import { FolderSetupStep } from '@/components/OnboardingSteps/FolderSetupStep';
import { AvatarSelectionStep } from '@/components/OnboardingSteps/AvatarSelectionStep';
import { ThemeSelectionStep } from '@/components/OnboardingSteps/ThemeSelectionStep';
import { STEPS } from '@/constants/steps';
import { UpdateStep } from '@/components/OnboardingSteps/UpdateStep';

interface OnboardingStepProps {
  stepIndex: number;
  stepName: string;
  onNext: () => void;
  onBack: () => void;
}

const VISIBLE_STEPS = [
  STEPS.AVATAR_SELECTION_STEP,
  STEPS.FOLDER_SETUP_STEP,
  STEPS.THEME_SELECTION_STEP,
];

export const OnboardingStep: React.FC<OnboardingStepProps> = ({
  stepIndex,
  stepName,
  onNext,
  onBack,
}) => {
  const sharedProps = {
    stepIndex,
    totalSteps: VISIBLE_STEPS.length,
    onNext,
    onBack,
  };

  const renderStepComponent = () => {
    switch (stepName) {
      case STEPS.AVATAR_SELECTION_STEP:
        return <AvatarSelectionStep {...sharedProps} />;
      case STEPS.FOLDER_SETUP_STEP:
        return <FolderSetupStep {...sharedProps} />;
      case STEPS.THEME_SELECTION_STEP:
        return <ThemeSelectionStep {...sharedProps} />;
      case STEPS.UPDATE_STEP:
        return <UpdateStep {...sharedProps} />;
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
