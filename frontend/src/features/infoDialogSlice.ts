import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface InfoDialogState {
  isOpen: boolean;
  title: string;
  message: string;
}

const initialState: InfoDialogState = {
  isOpen: false,
  title: '',
  message: '',
};

const infoDialogSlice = createSlice({
  name: 'infoDialog',
  initialState,
  reducers: {
    showInfoDialog(
      state,
      action: PayloadAction<{ title: string; message: string }>,
    ) {
      state.isOpen = true;
      state.title = action.payload.title;
      state.message = action.payload.message;
    },
    hideInfoDialog(state) {
      state.isOpen = false;
      state.title = '';
      state.message = '';
    },
  },
});

export const { showInfoDialog, hideInfoDialog } = infoDialogSlice.actions;
export default infoDialogSlice.reducer;
