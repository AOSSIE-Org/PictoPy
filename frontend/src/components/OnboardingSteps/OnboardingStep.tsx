import React from 'react';
import { FolderSetupStep } from '@/components/OnboardingSteps/FolderSetupStep';
import { UpdateStep } from '@/components/OnboardingSteps/UpdateStep';
import { STEPS } from '@/constants/steps';

interface OnboardingStepProps {
  stepIndex: number;
  stepName: string;
}
export const OnboardingStep: React.FC<OnboardingStepProps> = ({
  stepIndex,
  stepName,
}: OnboardingStepProps) => {
  console.log(
    `Rendering OnboardingStep: stepIndex=${stepIndex}, stepName=${stepName}`,
  );
  switch (stepName) {
    case STEPS.UPDATE_STEP:
      return <UpdateStep stepIndex={stepIndex} />;
    case STEPS.FOLDER_SETUP_STEP:
      return <FolderSetupStep stepIndex={stepIndex} />;
    default:
      return <div></div>;
  }
};
