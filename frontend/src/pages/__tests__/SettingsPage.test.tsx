import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import Settings from '../SettingsPage/Settings';

describe('Settings Page', () => {
  // shared setup for all tests
  const setupTest = () => {
    const user = userEvent.setup();
    render(<Settings />);
    return { user };
  };

  describe('Interaction Sanity', () => {
    describe('User Preferences Section', () => {
      test('YOLO model dropdown opens and shows options', async () => {
        const { user } = setupTest();

        const dropdownTrigger = screen.getByRole('button', {
          name: /nano|small|medium/i,
        });
        await user.click(dropdownTrigger);

        const menuItems = screen.getAllByRole('menuitem');
        expect(menuItems).toHaveLength(3);
        expect(menuItems[0]).toHaveTextContent('Nano');
        expect(menuItems[1]).toHaveTextContent('Small');
        expect(menuItems[2]).toHaveTextContent('Medium');
      });

      test('GPU Acceleration toggle changes state on click', async () => {
        const { user } = setupTest();

        const gpuSwitch = screen.getByRole('switch');
        expect(gpuSwitch).toHaveAttribute('aria-checked', 'false');

        await user.click(gpuSwitch);

        expect(gpuSwitch).toHaveAttribute('aria-checked', 'true');
      });
    });

    describe('Action Buttons', () => {
      const buttonCases = [
        { name: /add folders/i, label: 'Add Folders' },
        { name: /check for updates/i, label: 'Check for Updates' },
        { name: /recluster faces/i, label: 'Recluster Faces' },
      ];

      test.each(buttonCases)(
        '$label button does not crash when clicked',
        async ({ name }) => {
          const { user } = setupTest();

          const button = screen.getByRole('button', { name });

          await user.click(button);

          expect(button).toBeEnabled();
        },
      );
    });
  });

  describe('State-Level Verification', () => {
    describe('YOLO Model Selection', () => {
      const yoloSelectionCases = [
        { selectOption: 'small', expectedText: 'Small' },
        { selectOption: 'medium', expectedText: 'Medium' },
      ];

      test.each(yoloSelectionCases)(
        'selecting $expectedText updates dropdown display',
        async ({ selectOption, expectedText }) => {
          const { user } = setupTest();

          const dropdownTrigger = screen.getByRole('button', { name: /nano/i });
          expect(dropdownTrigger).toHaveTextContent('Nano');

          await user.click(dropdownTrigger);
          await user.click(
            screen.getByRole('menuitem', {
              name: new RegExp(selectOption, 'i'),
            }),
          );

          expect(dropdownTrigger).toHaveTextContent(expectedText);
        },
      );

      test('dropdown can be reopened after selection', async () => {
        const { user } = setupTest();

        const dropdownTrigger = screen.getByRole('button', { name: /nano/i });
        await user.click(dropdownTrigger);
        await user.click(screen.getByRole('menuitem', { name: /small/i }));

        // reopen and verify options still available
        await user.click(dropdownTrigger);
        expect(screen.getAllByRole('menuitem')).toHaveLength(3);
      });
    });

    describe('GPU Acceleration Toggle', () => {
      test('toggle cycles through ON/OFF states', async () => {
        const { user } = setupTest();

        const gpuSwitch = screen.getByRole('switch');
        expect(gpuSwitch).toHaveAttribute('aria-checked', 'false');

        await user.click(gpuSwitch);
        expect(gpuSwitch).toHaveAttribute('aria-checked', 'true');

        await user.click(gpuSwitch);
        expect(gpuSwitch).toHaveAttribute('aria-checked', 'false');
      });
    });
  });

  /**
   * TODO: System integrations (future scope)
   * Belongs in E2E tests (Playwright/Cypress) rather than Jest
   * - Full user flows with mocked/real backend
   * - Update preferences API verification
   * - Check for updates flow
   */
});
