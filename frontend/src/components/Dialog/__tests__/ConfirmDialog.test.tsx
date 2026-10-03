import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmDialog } from '../../Dialog/ConfirmDialog';

const renderDialog = (
  props: Partial<React.ComponentProps<typeof ConfirmDialog>>,
) =>
  render(
    <ConfirmDialog
      open
      onOpenChange={jest.fn()}
      title="Delete photo"
      description="Pick what happens to the file."
      confirmLabel="Delete"
      onConfirm={jest.fn()}
      {...props}
    />,
  );

describe('ConfirmDialog checkbox', () => {
  test('is absent unless a label is given, so existing callers are unaffected', () => {
    renderDialog({});

    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
  });

  test('renders unchecked by default with its label and hint', () => {
    renderDialog({
      checkboxLabel: 'Also delete the file',
      checkboxHint: 'The file stays in its folder.',
    });

    expect(screen.getByRole('checkbox')).not.toBeChecked();
    expect(screen.getByText('Also delete the file')).toBeInTheDocument();
    expect(
      screen.getByText('The file stays in its folder.'),
    ).toBeInTheDocument();
  });

  test('reports a toggle to the caller', () => {
    const onCheckboxChange = jest.fn();
    renderDialog({ checkboxLabel: 'Also delete the file', onCheckboxChange });

    fireEvent.click(screen.getByRole('checkbox'));

    expect(onCheckboxChange).toHaveBeenCalledWith(true);
  });

  test('shows the checked state the caller passes in', () => {
    renderDialog({
      checkboxLabel: 'Also delete the file',
      checkboxChecked: true,
    });

    expect(screen.getByRole('checkbox')).toBeChecked();
  });
});
