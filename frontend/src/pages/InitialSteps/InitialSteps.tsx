import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { Step } from '@/types/steps';
import { ROUTES } from '@/constants/routes';
import { STEPS } from '@/constants/steps';

export const InitialSteps: React.FC = () => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [activeSteps] = useState<Step[]>(STEPS);
  const navigate = useNavigate();

  const handleNext = () => {
    if (currentStepIndex >= activeSteps.length - 1) {
      navigate(`/${ROUTES.LAYOUT.HOME}`);
    } else {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const CurrentStep = activeSteps[currentStepIndex]?.component;
  if (CurrentStep) return <CurrentStep onNext={handleNext} />;
};
