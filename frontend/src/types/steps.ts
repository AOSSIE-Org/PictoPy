import { ComponentType } from 'react';
export interface StepProps {
  onNext: () => void;
}

export interface Step {
  id: string;
  component: ComponentType<StepProps>;
}
