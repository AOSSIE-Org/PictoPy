import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { InfoDialogProps, InfoDialogVariant } from '@/types/infoDialog';

const initialState: InfoDialogProps = {
  isOpen: false,
  title: '',
  message: '',
  variant: 'info',
};

const infoDialogSlice = createSlice({
  name: 'infoDialog',
  initialState,
  reducers: {
    showInfoDialog(
      state,
      action: PayloadAction<{
        title: string;
        message: string;
        variant?: InfoDialogVariant;
      }>,
    ) {
      state.isOpen = true;
      state.title = action.payload.title;
      state.message = action.payload.message;
      state.variant = action.payload.variant || 'info';
    },
    hideInfoDialog(state) {
      state.isOpen = false;
      state.title = '';
      state.message = '';
      state.variant = 'info';
    },
  },
});

export const { showInfoDialog, hideInfoDialog } = infoDialogSlice.actions;
export default infoDialogSlice.reducer;
