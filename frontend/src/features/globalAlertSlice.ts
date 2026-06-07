import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface GlobalAlertState {
  isOpen: boolean;
  title: string;
  message: string;
}

const initialState: GlobalAlertState = {
  isOpen: false,
  title: '',
  message: '',
};

const globalAlertSlice = createSlice({
  name: 'globalAlert',
  initialState,
  reducers: {
    showGlobalAlert(
      state,
      action: PayloadAction<{
        title: string;
        message: string;
      }>,
    ) {
      state.isOpen = true;
      state.title = action.payload.title;
      state.message = action.payload.message;
    },
    hideGlobalAlert(state) {
      state.isOpen = false;
      state.title = '';
      state.message = '';
    },
  },
});

export const { showGlobalAlert, hideGlobalAlert } = globalAlertSlice.actions;
export default globalAlertSlice.reducer;
