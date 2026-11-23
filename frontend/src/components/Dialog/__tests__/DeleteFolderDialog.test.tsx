import { render, screen, fireEvent, act } from '@testing-library/react';
import { DeleteFolderDialog } from '../DeleteFolderDialog';

const renderDialog = (
  props: Partial<React.ComponentProps<typeof DeleteFolderDialog>> = {},
) =>
  render(
    <DeleteFolderDialog
      open
      onOpenChange={jest.fn()}
      folderPath="/home/user/Photos"
      subfolderCount={3}
      onConfirm={jest.fn()}
      {...props}
    />,
  );

describe('DeleteFolderDialog', () => {
  test('names the folder and offers to delete the subfolders', () => {
    renderDialog();

    expect(screen.getByText(/"Photos"/)).toBeInTheDocument();
    expect(screen.getByText('Also delete 3 subfolders')).toBeInTheDocument();
  });

  test('handles Windows paths and a single subfolder', () => {
    renderDialog({ folderPath: 'C:\\Users\\me\\Pictures', subfolderCount: 1 });

    expect(screen.getByText(/"Pictures"/)).toBeInTheDocument();
    expect(screen.getByText('Also delete 1 subfolder')).toBeInTheDocument();
  });

  test('keeps subfolders by default', async () => {
    const onConfirm = jest.fn();
    renderDialog({ onConfirm });

    expect(screen.getByLabelText('Also delete 3 subfolders')).not.toBeChecked();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    });

    expect(onConfirm).toHaveBeenCalledWith(false, false);
  });

  test('deletes subfolders when the box is ticked', async () => {
    const onConfirm = jest.fn();
    renderDialog({ onConfirm });

    fireEvent.click(screen.getByLabelText('Also delete 3 subfolders'));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    });

    expect(onConfirm).toHaveBeenCalledWith(true, false);
  });

  test('cancel does not confirm', () => {
    const onConfirm = jest.fn();
    const onOpenChange = jest.fn();
    renderDialog({ onConfirm, onOpenChange });

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(onConfirm).not.toHaveBeenCalled();
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  test('starts from the default it is given', () => {
    renderDialog({ defaultDeleteSubfolders: true });

    expect(screen.getByLabelText('Also delete 3 subfolders')).toBeChecked();
  });

  test('reports "Don\'t show again" when confirmed', async () => {
    const onConfirm = jest.fn();
    renderDialog({ onConfirm });

    fireEvent.click(screen.getByLabelText("Don't show again"));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    });

    expect(onConfirm).toHaveBeenCalledWith(false, true);
  });
});
