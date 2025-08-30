import { RootState } from '@/app/store';

// Basic selectors
export const selectCurrentStepIndex = (state: RootState) =>
  state.onboarding.currentStepIndex;

export const selectCurrentStepName = (state: RootState) =>
  state.onboarding.currentStepName;

export const selectStepStatus = (state: RootState) =>
  state.onboarding.stepStatus;

export const selectAvatar = (state: RootState) => state.onboarding.avatar;

export const selectName = (state: RootState) => state.onboarding.name;
