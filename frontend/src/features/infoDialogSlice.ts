import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface InfoDialogState {
  open: boolean;
  title: string;
  description: string;
  variant?: 'default' | 'success' | 'warning' | 'destructive';
}

const initialState: InfoDialogState = {
  open: false,
  title: '',
  description: '',
  variant: 'default',
};

const infoDialogSlice = createSlice({
  name: 'infoDialog',
  initialState,
  reducers: {
    showInfoDialog(
      state,
      action: PayloadAction<{
        title: string;
        description: string;
        variant?: 'default' | 'success' | 'warning' | 'destructive';
      }>,
    ) {
      state.open = true;
      state.title = action.payload.title;
      state.description = action.payload.description;
      state.variant = action.payload.variant || 'default';
    },
    hideInfoDialog(state) {
      state.open = false;
      state.title = '';
      state.description = '';
      state.variant = 'default';
    },
  },
});

export const { showInfoDialog, hideInfoDialog } = infoDialogSlice.actions;
export default infoDialogSlice.reducer;
