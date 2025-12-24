import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { InfoDialogProps, InfoDialogVariant } from '@/types/infoDialog';

const initialState: InfoDialogProps = {
  isOpen: false,
  title: '',
  message: '',
  variant: 'info',
  showCloseButton: true,
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
        showCloseButton?: boolean;
      }>,
    ) {
      state.isOpen = true;
      state.title = action.payload.title;
      state.message = action.payload.message;
      state.variant = action.payload.variant || 'info';
      state.showCloseButton = action.payload.showCloseButton ?? true;
    },
    hideInfoDialog(state) {
      state.isOpen = false;
      state.title = '';
      state.message = '';
      state.variant = state.variant || 'info';
      state.showCloseButton = true;
    },
  },
});

export const { showInfoDialog, hideInfoDialog } = infoDialogSlice.actions;
export default infoDialogSlice.reducer;
