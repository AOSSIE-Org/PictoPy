import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { STEPS } from '@/constants/steps';

const STEP_NAMES = Object.values(STEPS);

interface OnboardingState {
  currentStepIndex: number;
  currentStepName: string;
  stepStatus: boolean[];
  avatar: string | null;
  name: string;
  isEditing: boolean;
}

const initialState: OnboardingState = {
  currentStepIndex: 0,
  currentStepName: STEP_NAMES[0],
  stepStatus: STEP_NAMES.map(() => false),
  avatar: localStorage.getItem('avatar'),
  name: localStorage.getItem('name') || '',
  isEditing: false,
};
const onboardingSlice = createSlice({
  name: 'onboarding',
  initialState,
  reducers: {
    setAvatar(state, action: PayloadAction<string>) {
      state.avatar = action.payload;
    },
    setName(state, action: PayloadAction<string>) {
      state.name = action.payload;
    },
    setIsEditing(state, action: PayloadAction<boolean>) {
      state.isEditing = action.payload;
    },
    markCompleted(state, action: PayloadAction<number>) {
      const stepIndex = action.payload;
      if (stepIndex >= 0 && stepIndex < state.stepStatus.length) {
        state.stepStatus[stepIndex] = true;
      } else {
        console.warn(
          `Invalid step index: ${stepIndex}. Valid range: 0-${state.stepStatus.length - 1}`,
        );
      }
      state.currentStepIndex = state.stepStatus.findIndex((status) => !status);
      state.currentStepName = STEP_NAMES[state.currentStepIndex] || '';
    },
    previousStep(state) {
      const lastCompletedIndex = state.stepStatus.lastIndexOf(true);
      if (lastCompletedIndex !== -1) {
        state.stepStatus[lastCompletedIndex] = false;
      }
      state.currentStepIndex = state.stepStatus.findIndex((status) => !status);
      state.currentStepName = STEP_NAMES[state.currentStepIndex] || '';
    },
  },
});

export const { setAvatar, setName, setIsEditing, markCompleted, previousStep } =
  onboardingSlice.actions;

export default onboardingSlice.reducer;
