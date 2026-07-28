import { render, screen, fireEvent } from '@testing-library/react';
import { VideoInfoPanel } from '../VideoInfoPanel';
import { Video } from '@/types/Media';

const makeVideo = (tags: string[]): Video => ({
  id: 'v1',
  path: 'C:\\videos\\v1.mp4',
  thumbnailPath: null,
  folder_id: 'folder-1',
  metadata: {
    name: 'v1.mp4',
    date_created: '2026-01-01T00:00:00',
    width: 1920,
    height: 1080,
    duration: 60,
    fps: 30,
    file_location: 'C:\\videos\\v1.mp4',
    file_size: 1024,
    item_type: 'video/mp4',
  },
  isFavourite: false,
  tags,
});

const renderPanel = (tags: string[]) =>
  render(
    <VideoInfoPanel
      show
      onClose={jest.fn()}
      video={makeVideo(tags)}
      currentIndex={0}
      totalVideos={1}
    />,
  );

describe('VideoInfoPanel tag list', () => {
  test('shows all tags and no toggle when there are 3 or fewer', () => {
    renderPanel(['alpha', 'beta', 'gamma']);

    expect(screen.getByText('alpha')).toBeInTheDocument();
    expect(screen.getByText('beta')).toBeInTheDocument();
    expect(screen.getByText('gamma')).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /show more/i }),
    ).not.toBeInTheDocument();
  });

  test('truncates to the first 3 tags and shows a "show more" toggle when there are more than 3', () => {
    renderPanel(['alpha', 'beta', 'gamma', 'delta', 'epsilon']);

    expect(screen.getByText('alpha')).toBeInTheDocument();
    expect(screen.getByText('beta')).toBeInTheDocument();
    expect(screen.getByText('gamma')).toBeInTheDocument();
    // Beyond the first 3 are hidden until expanded.
    expect(screen.queryByText('delta')).not.toBeInTheDocument();
    expect(screen.queryByText('epsilon')).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /show more/i }),
    ).toBeInTheDocument();
  });

  test('"show more" reveals all tags and flips the toggle to "show less"', () => {
    renderPanel(['alpha', 'beta', 'gamma', 'delta', 'epsilon']);

    fireEvent.click(screen.getByRole('button', { name: /show more/i }));

    expect(screen.getByText('delta')).toBeInTheDocument();
    expect(screen.getByText('epsilon')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /show less/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /show more/i }),
    ).not.toBeInTheDocument();
  });

  test('"show less" collapses back to the first 3 tags', () => {
    renderPanel(['alpha', 'beta', 'gamma', 'delta', 'epsilon']);

    fireEvent.click(screen.getByRole('button', { name: /show more/i }));
    fireEvent.click(screen.getByRole('button', { name: /show less/i }));

    expect(screen.queryByText('delta')).not.toBeInTheDocument();
    expect(screen.queryByText('epsilon')).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /show more/i }),
    ).toBeInTheDocument();
  });
});
