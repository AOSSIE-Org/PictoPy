import React, { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { ROUTES } from '@/constants/routes';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import { OnboardingStep } from '@/components/OnboardingSteps/OnboardingStep';
export const InitialSteps: React.FC = () => {
  const navigate = useNavigate();
  const { currentStepIndex, currentStepName } = useSelector(
    (state: RootState) => state.onboarding,
  );
  useEffect(() => {
    if (currentStepIndex === -1) {
      navigate(ROUTES.HOME);
    }
  }, [currentStepIndex]);

  return (
    <OnboardingStep stepIndex={currentStepIndex} stepName={currentStepName} />
  );
};
