import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { STEPS } from '@/constants/steps';

const STEP_NAMES = Object.values(STEPS);

interface OnboardingState {
  currentStepIndex: number;
  currentStepName: string;
  stepStatus: boolean[];
}
const initialState: OnboardingState = {
  currentStepIndex: 0,
  currentStepName: STEP_NAMES[0],
  stepStatus: STEP_NAMES.map(() => false),
};

const onboardingSlice = createSlice({
  name: 'onboarding',
  initialState,
  reducers: {
    markCompleted(state, action: PayloadAction<number>) {
      const stepIndex = action.payload;
      if (stepIndex >= 0 && stepIndex < state.stepStatus.length) {
        state.stepStatus[stepIndex] = true;
      }
      // Update current step index and name
      state.currentStepIndex = state.stepStatus.findIndex((status) => !status);
      state.currentStepName = STEP_NAMES[state.currentStepIndex];
    },
    previousStep(state) {
      //Mark the last completed step as incomplete
      const lastCompletedIndex = state.stepStatus.lastIndexOf(true);
      if (lastCompletedIndex !== -1) {
        state.stepStatus[lastCompletedIndex] = false;
      }
      // Update current step index and name
      state.currentStepIndex = state.stepStatus.findIndex((status) => !status);
      state.currentStepName = STEP_NAMES[state.currentStepIndex];
    },
  },
});

export const { markCompleted, previousStep } = onboardingSlice.actions;
export default onboardingSlice.reducer;
