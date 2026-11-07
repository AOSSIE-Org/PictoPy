import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MediaInfoPanel } from '../MediaInfoPanel';
import { Image } from '@/types/Media';
import { revealItemInDir } from '@tauri-apps/plugin-opener';

jest.mock('@tauri-apps/plugin-shell', () => ({
  open: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('@tauri-apps/plugin-opener', () => ({
  revealItemInDir: jest.fn().mockResolvedValue(undefined),
}));

const mockRevealItemInDir = jest.mocked(revealItemInDir);

const makeImage = (tags: string[]): Image => ({
  id: 'img1',
  path: 'C:\\pics\\img1.jpg',
  thumbnailPath: 'C:\\pics\\thumb\\img1.jpg',
  folder_id: 'folder-1',
  isTagged: true,
  metadata: {
    name: 'img1.jpg',
    date_created: '2026-01-01T00:00:00',
    width: 1920,
    height: 1080,
    file_location: 'C:\\pics\\img1.jpg',
    file_size: 1024,
    item_type: 'image/jpeg',
  },
  isFavourite: false,
  tags,
});

const renderPanel = (tags: string[]) =>
  render(
    <MediaInfoPanel
      show
      onClose={jest.fn()}
      currentImage={makeImage(tags)}
      currentIndex={0}
      totalImages={1}
    />,
  );

describe('MediaInfoPanel tag list', () => {
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
    expect(screen.getByText('gamma')).toBeInTheDocument();
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

  test('resets to the compact default when a different image is shown', () => {
    const first = makeImage(['alpha', 'beta', 'gamma', 'delta', 'epsilon']);
    const second: Image = {
      ...makeImage(['one', 'two', 'three', 'four']),
      id: 'img2',
    };
    const { rerender } = render(
      <MediaInfoPanel
        show
        onClose={jest.fn()}
        currentImage={first}
        currentIndex={0}
        totalImages={2}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /show more/i }));
    expect(screen.getByText('epsilon')).toBeInTheDocument();

    rerender(
      <MediaInfoPanel
        show
        onClose={jest.fn()}
        currentImage={second}
        currentIndex={1}
        totalImages={2}
      />,
    );

    expect(screen.queryByText('four')).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /show more/i }),
    ).toBeInTheDocument();
  });
});

describe('MediaInfoPanel Open Original File button', () => {
  beforeEach(() => {
    mockRevealItemInDir.mockReset();
    mockRevealItemInDir.mockResolvedValue(undefined);
  });

  test.each([
    ['Windows', 'C:\\Library\\original1.jpg'],
    ['POSIX', '/home/user/pics/img1.jpg'],
    ['Windows root', 'C:\\img1.jpg'],
    ['POSIX root', '/img1.jpg'],
    ['Windows spaces and Unicode', 'C:\\My Photos\\旅行\\été.jpg'],
    ['POSIX spaces and Unicode', '/home/user/My Photos/旅行/été.jpg'],
  ])('reveals the full %s path exactly once', async (_description, path) => {
    const image: Image = { ...makeImage(['alpha']), path };
    render(
      <MediaInfoPanel
        show
        onClose={jest.fn()}
        currentImage={image}
        currentIndex={0}
        totalImages={1}
      />,
    );

    fireEvent.click(
      screen.getByRole('button', { name: /open original file/i }),
    );

    await waitFor(() => {
      expect(mockRevealItemInDir).toHaveBeenCalledTimes(1);
      expect(mockRevealItemInDir).toHaveBeenCalledWith(path);
    });
  });

  test('reveals the newly selected image after rerendering', async () => {
    const first: Image = { ...makeImage(['alpha']), path: '/pics/first.jpg' };
    const second: Image = {
      ...makeImage(['beta']),
      id: 'img2',
      path: '/pics/second.jpg',
    };
    const { rerender } = render(
      <MediaInfoPanel
        show
        onClose={jest.fn()}
        currentImage={first}
        currentIndex={0}
        totalImages={2}
      />,
    );

    fireEvent.click(
      screen.getByRole('button', { name: /open original file/i }),
    );
    await waitFor(() => {
      expect(mockRevealItemInDir).toHaveBeenNthCalledWith(1, first.path);
    });

    rerender(
      <MediaInfoPanel
        show
        onClose={jest.fn()}
        currentImage={second}
        currentIndex={1}
        totalImages={2}
      />,
    );
    fireEvent.click(
      screen.getByRole('button', { name: /open original file/i }),
    );

    await waitFor(() => {
      expect(mockRevealItemInDir).toHaveBeenCalledTimes(2);
      expect(mockRevealItemInDir).toHaveBeenNthCalledWith(2, second.path);
    });
  });

  test.each<{ description: string; image: Image | null }>([
    { description: 'no image is selected', image: null },
    {
      description: 'the selected image has an empty path',
      image: { ...makeImage(['alpha']), path: '' },
    },
  ])('does not reveal when $description', ({ image }) => {
    render(
      <MediaInfoPanel
        show
        onClose={jest.fn()}
        currentImage={image}
        currentIndex={0}
        totalImages={1}
      />,
    );

    fireEvent.click(
      screen.getByRole('button', { name: /open original file/i }),
    );

    expect(mockRevealItemInDir).not.toHaveBeenCalled();
  });

  test('handles and logs a rejected reveal request', async () => {
    const error = new Error('Unable to reveal image');
    mockRevealItemInDir.mockRejectedValueOnce(error);
    const consoleError = jest
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    try {
      renderPanel(['alpha']);
      fireEvent.click(
        screen.getByRole('button', { name: /open original file/i }),
      );

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledTimes(1);
        expect(consoleError).toHaveBeenCalledWith(
          'Failed to open folder:',
          error,
        );
      });
      expect(mockRevealItemInDir).toHaveBeenCalledTimes(1);
      expect(mockRevealItemInDir).toHaveBeenCalledWith(
        makeImage(['alpha']).path,
      );
    } finally {
      consoleError.mockRestore();
    }
  });
});
