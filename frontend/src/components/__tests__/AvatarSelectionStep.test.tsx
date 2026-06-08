import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { AvatarSelectionStep } from '@/components/OnboardingSteps/AvatarSelectionStep';

const VALID_30 = 'a'.repeat(30);
const INVALID_31 = 'a'.repeat(31);
const ERROR_MSG = 'A single word in your name cannot exceed 30 characters.';

beforeEach(() => localStorage.clear());

describe('Name validation - AvatarSelectionStep', () => {
  const setup = () => {
    const user = userEvent.setup();
    render(
      <AvatarSelectionStep
        stepIndex={0}
        totalSteps={4}
        currentStepDisplayIndex={0}
      />,
    );
    const input = screen.getByPlaceholderText('Enter your name');
    return { user, input };
  };

  test('30-character word is valid - no error shown', async () => {
    const { user, input } = setup();
    await user.type(input, VALID_30);
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });

  test('31-character word shows error and disables Next button', async () => {
    const { user, input } = setup();
    await user.type(input, INVALID_31);
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
  });

  test('multi-space input is handled gracefully - no error', async () => {
    const { user, input } = setup();
    await user.type(input, 'John   Doe');
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });

  test('recovery - valid input after invalid clears error', async () => {
    const { user, input } = setup();
    await user.type(input, INVALID_31);
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument();
    await user.clear(input);
    await user.type(input, 'John');
    expect(screen.queryByText(ERROR_MSG)).not.toBeInTheDocument();
  });
});