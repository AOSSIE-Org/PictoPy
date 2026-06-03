import { render, screen, fireEvent } from '@/test-utils';
import { AvatarSelectionStep } from '@/components/OnboardingSteps/AvatarSelectionStep';
import AccountSettingsCard from '@/pages/SettingsPage/components/AccountSettingsCard';

const VALID_30 = 'a'.repeat(30);
const INVALID_31 = 'a'.repeat(31);
const ERROR_MSG = 'A single word in your name cannot exceed 30 characters.';

beforeEach(() => localStorage.clear());

//AvatarSelectionStep

describe('Name validation - AvatarSelectionStep', () => {
  const setup = () => {
    render(
      <AvatarSelectionStep
        stepIndex={0}
        totalSteps={4}
        currentStepDisplayIndex={0}
      />,
    );
    fireEvent.click(screen.getAllByAltText('Avatar')[0]);
    const input = screen.getByPlaceholderText('Enter your name');
    return { input };
  };

  test('30-character word is valid - no error shown', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: VALID_30 } });
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled();
  });

  test('31-character word shows error and disables Next button', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: INVALID_31 } });
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
  });

  test('multi-space input is handled gracefully - no error', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: 'John   Doe' } });
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });

  test('recovery - valid input after invalid clears error and re-enables Next', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: INVALID_31 } });
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
    fireEvent.change(input, { target: { value: 'John' } });
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled();
  });
});

//AccountSettingsCard

describe('Name validation - AccountSettingsCard', () => {
  const setup = () => {
    render(<AccountSettingsCard />);
    fireEvent.click(screen.getAllByAltText('Avatar')[0]);
    const input = screen.getByPlaceholderText('Enter your name');
    return { input };
  };

  test('30 character word is valid - no error shown', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: VALID_30 } });
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /save changes/i }),
    ).not.toBeDisabled();
  });

  test('31 character word shows error and disables Save Changes button', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: INVALID_31 } });
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /save changes/i }),
    ).toBeDisabled();
  });

  test('multi-space input is handled gracefully - no error', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: 'John   Doe' } });
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });

  test('recovery - valid input after invalid clears error and re-enables Save', () => {
    const { input } = setup();
    fireEvent.change(input, { target: { value: INVALID_31 } });
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /save changes/i }),
    ).toBeDisabled();
    fireEvent.change(input, { target: { value: 'John' } });
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /save changes/i }),
    ).not.toBeDisabled();
  });
});
