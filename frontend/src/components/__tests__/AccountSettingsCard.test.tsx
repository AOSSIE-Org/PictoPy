import { render, screen, act } from '@/test-utils';
import { within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createRef } from 'react';
import AccountSettingsCard, {
  AccountSettingsCardHandle,
} from '@/pages/SettingsPage/components/AccountSettingsCard';

const VALID_30 = 'a'.repeat(30);
const INVALID_31 = 'a'.repeat(31);
const ERROR_MSG = 'A single word in your name cannot exceed 30 characters.';

beforeEach(() => localStorage.clear());

describe('Name validation - AccountSettingsCard', () => {
  const setup = async () => {
    const user = userEvent.setup();
    render(<AccountSettingsCard />);
    await user.click(screen.getByRole('button', { name: /edit name/i }));
    const input = screen.getByPlaceholderText('Enter your name');
    return { user, input };
  };

  test('30-character word is valid - no error shown', async () => {
    const { user, input } = await setup();
    await user.type(input, VALID_30);
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });

  test('31-character word shows error', async () => {
    const { user, input } = await setup();
    await user.type(input, INVALID_31);
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
  });

  test('multi-space input is handled gracefully - no error', async () => {
    const { user, input } = await setup();
    await user.type(input, 'John   Doe');
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });

  test('recovery - valid input after invalid clears error', async () => {
    const { user, input } = await setup();
    await user.type(input, INVALID_31);
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
    await user.clear(input);
    await user.type(input, 'John');
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });

  test('name edit shows Enter/Esc helper text', async () => {
    await setup();
    expect(
      screen.getByText('Press Enter to save • Esc to cancel'),
    ).toBeInTheDocument();
  });
});

describe('Save Changes button - AccountSettingsCard', () => {
  test('is always visible', () => {
    render(<AccountSettingsCard />);
    expect(
      screen.getByRole('button', { name: 'Save Changes' }),
    ).toBeInTheDocument();
  });

  test('is disabled until an avatar is selected', () => {
    render(<AccountSettingsCard />);
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeDisabled();
  });

  test('enables after selecting an avatar', async () => {
    const user = userEvent.setup();
    render(<AccountSettingsCard />);
    const avatarButtons = screen.getAllByRole('button', { name: 'Avatar' });
    await user.click(avatarButtons[0]);
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeEnabled();
  });
});

describe('Unsaved-changes leave guard - AccountSettingsCard', () => {
  test('requestLeave proceeds immediately when there are no unsaved changes', () => {
    const ref = createRef<AccountSettingsCardHandle>();
    render(<AccountSettingsCard ref={ref} />);
    const onLeave = jest.fn();
    act(() => {
      ref.current?.requestLeave(onLeave);
    });
    expect(onLeave).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('Unsaved changes')).not.toBeInTheDocument();
  });

  test('requestLeave shows a dialog when there are unsaved changes; Discard proceeds', async () => {
    const user = userEvent.setup();
    const ref = createRef<AccountSettingsCardHandle>();
    render(<AccountSettingsCard ref={ref} />);

    const avatarButtons = screen.getAllByRole('button', { name: 'Avatar' });
    await user.click(avatarButtons[0]);
    expect(ref.current?.hasUnsavedChanges).toBe(true);

    const onLeave = jest.fn();
    act(() => {
      ref.current?.requestLeave(onLeave);
    });
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
    expect(onLeave).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /^discard$/i }));
    expect(onLeave).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('Unsaved changes')).not.toBeInTheDocument();
  });

  test('Cancel keeps the changes and does not leave', async () => {
    const user = userEvent.setup();
    const ref = createRef<AccountSettingsCardHandle>();
    render(<AccountSettingsCard ref={ref} />);

    const avatarButtons = screen.getAllByRole('button', { name: 'Avatar' });
    await user.click(avatarButtons[0]);

    const onLeave = jest.fn();
    act(() => {
      ref.current?.requestLeave(onLeave);
    });

    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: /^cancel$/i }));

    expect(onLeave).not.toHaveBeenCalled();
    expect(ref.current?.hasUnsavedChanges).toBe(true);
  });
});
