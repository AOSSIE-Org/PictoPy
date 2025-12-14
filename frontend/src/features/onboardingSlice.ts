import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { STEPS } from '@/constants/steps';

const STEP_NAMES = Object.values(STEPS);

interface OnboardingState {
  currentStepIndex: number;
  currentStepName: string;
  stepStatus: boolean[];
  avatar: string | null;
  name: string;
}

const initialState: OnboardingState = {
  currentStepIndex: 0,
  currentStepName: STEP_NAMES[0],
  stepStatus: STEP_NAMES.map(() => false),
  avatar: localStorage.getItem('avatar'),
  name: localStorage.getItem('name') || '',
};

const onboardingSlice = createSlice({
  name: 'onboarding',
  initialState,
  reducers: {
    setAvatar(state, action: PayloadAction<string>) {
      state.avatar = action.payload;
      localStorage.setItem('avatar', action.payload);
    },

    setName(state, action: PayloadAction<string>) {
      state.name = action.payload;
      localStorage.setItem('name', action.payload);
    },

    /** ✅ LOGOUT / RESET */
    resetOnboarding() {
      localStorage.removeItem('avatar');
      localStorage.removeItem('name');
      return initialState;
    },

    markCompleted(state, action: PayloadAction<number>) {
      const index = action.payload;
      if (index >= 0 && index < state.stepStatus.length) {
        state.stepStatus[index] = true;
      }
      state.currentStepIndex = state.stepStatus.findIndex((s) => !s);
      state.currentStepName = STEP_NAMES[state.currentStepIndex] || '';
    },

    previousStep(state) {
      const lastCompleted = state.stepStatus.lastIndexOf(true);
      if (lastCompleted !== -1) {
        state.stepStatus[lastCompleted] = false;
      }
      state.currentStepIndex = state.stepStatus.findIndex((s) => !s);
      state.currentStepName = STEP_NAMES[state.currentStepIndex] || '';
    },
  },
});

export const {
  setAvatar,
  setName,
  resetOnboarding,
  markCompleted,
  previousStep,
} = onboardingSlice.actions;

export default onboardingSlice.reducer;
