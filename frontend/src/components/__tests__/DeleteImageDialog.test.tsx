import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import DeleteImagesDialog from '../FolderPicker/DeleteImageDialog';

describe('DeleteImagesDialog', () => {
  const mockSetIsOpen = jest.fn();
  const mockExecuteDeleteImages = jest.fn();

  const defaultProps = {
    isOpen: true,
    setIsOpen: mockSetIsOpen,
    executeDeleteImages: mockExecuteDeleteImages,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('renders confirmation text when open', () => {
      render(<DeleteImagesDialog {...defaultProps} />);

      expect(
        screen.getByText(
          'Do you also want to delete these images from Device ?',
        ),
      ).toBeInTheDocument();
    });

    test('does not render content when closed', () => {
      render(<DeleteImagesDialog {...defaultProps} isOpen={false} />);

      expect(
        screen.queryByText(
          'Do you also want to delete these images from Device ?',
        ),
      ).not.toBeInTheDocument();
    });

    test('renders Yes and No buttons', () => {
      render(<DeleteImagesDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /yes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /no/i })).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    test('clicking Yes calls executeDeleteImages(true) and closes dialog', async () => {
      const user = userEvent.setup();
      render(<DeleteImagesDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /yes/i }));

      expect(mockExecuteDeleteImages).toHaveBeenCalledWith(true);
      expect(mockSetIsOpen).toHaveBeenCalledWith(false);
    });

    test('clicking No calls executeDeleteImages(false) and closes dialog', async () => {
      const user = userEvent.setup();
      render(<DeleteImagesDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /no/i }));

      expect(mockExecuteDeleteImages).toHaveBeenCalledWith(false);
      expect(mockSetIsOpen).toHaveBeenCalledWith(false);
    });
  });
});
