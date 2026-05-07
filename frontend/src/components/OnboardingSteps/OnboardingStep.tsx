import '@/App.css';
import React from 'react';

import { FolderSetupStep } from '@/components/OnboardingSteps/FolderSetupStep';
import { AvatarSelectionStep } from '@/components/OnboardingSteps/AvatarSelectionStep';
import { ThemeSelectionStep } from '@/components/OnboardingSteps/ThemeSelectionStep';
import { STEPS } from '@/constants/steps';
import { UpdateStep } from '@/components/OnboardingSteps/UpdateStep';
import { ServerCheck } from './ServerCheck';
import { AIModelSetupStep } from '@/components/OnboardingSteps/AIModelSetupStep';
import type { OnboardingStepName } from '@/features/onboardingSlice';

interface OnboardingStepProps {
  stepIndex: number;
  stepName: OnboardingStepName;
}

const VISIBLE_STEPS = [
  STEPS.AVATAR_SELECTION_STEP,
  STEPS.FOLDER_SETUP_STEP,
  STEPS.THEME_SELECTION_STEP,
  STEPS.MODEL_SETUP_STEP,
] as const;

type VisibleStepName = (typeof VISIBLE_STEPS)[number];

const isVisibleStepName = (
  step: OnboardingStepName,
): step is VisibleStepName => VISIBLE_STEPS.includes(step as VisibleStepName);

export const OnboardingStep: React.FC<OnboardingStepProps> = ({
  stepIndex,
  stepName,
}) => {
  const visibleStepIndex = isVisibleStepName(stepName)
    ? VISIBLE_STEPS.indexOf(stepName)
    : -1;

  const sharedProps = {
    stepIndex,
    totalSteps: VISIBLE_STEPS.length,
    currentStepDisplayIndex: visibleStepIndex,
  };

  const renderStepComponent = () => {
    switch (stepName) {
      case STEPS.AVATAR_SELECTION_STEP:
        return <AvatarSelectionStep {...sharedProps} />;
      case STEPS.FOLDER_SETUP_STEP:
        return <FolderSetupStep {...sharedProps} />;
      case STEPS.THEME_SELECTION_STEP:
        return <ThemeSelectionStep {...sharedProps} />;
      case STEPS.MODEL_SETUP_STEP:
        return <AIModelSetupStep {...sharedProps} />;
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
