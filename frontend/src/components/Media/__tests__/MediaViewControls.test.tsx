import { render, screen, fireEvent } from '@testing-library/react';
import { MediaViewControls } from '../MediaViewControls';

const renderControls = (onDelete?: () => void) =>
  render(
    <MediaViewControls
      showInfo={false}
      onToggleInfo={jest.fn()}
      onToggleFavourite={jest.fn()}
      onOpenFolder={jest.fn().mockResolvedValue(undefined)}
      onDelete={onDelete}
      isFavourite={false}
      isSlideshowActive={false}
      onToggleSlideshow={jest.fn()}
      onClose={jest.fn()}
    />,
  );

describe('MediaViewControls delete button', () => {
  test('is hidden when no delete handler is given', () => {
    renderControls();

    expect(
      screen.queryByRole('button', { name: 'Delete' }),
    ).not.toBeInTheDocument();
  });

  test('calls the delete handler when clicked', () => {
    const onDelete = jest.fn();
    renderControls(onDelete);

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  test('sits immediately left of the open folder button', () => {
    renderControls(jest.fn());

    const labels = screen
      .getAllByRole('button')
      .map((button) => button.getAttribute('aria-label'));

    expect(labels.indexOf('Delete')).toBe(labels.indexOf('Open Folder') - 1);
  });
});
