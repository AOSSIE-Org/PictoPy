import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/test-utils';
import { addImagesToAlbum, fetchAllImages } from '@/api/api-functions';
import type { Image } from '@/types/Media';
import { AddImagesToAlbumDialog } from '../AddImagesToAlbumDialog';

jest.mock('@/api/api-functions', () => ({
  addImagesToAlbum: jest.fn(),
  fetchAllImages: jest.fn(),
}));

jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
  convertFileSrc: (path: string) => `tauri-converted://${path}`,
}));

const mockFetchAllImages = jest.mocked(fetchAllImages);
const mockAddImagesToAlbum = jest.mocked(addImagesToAlbum);

const images: Image[] = [
  {
    id: 'windows-image',
    path: String.raw`C:\Users\me\Pictures\Vacation\sunset.jpg`,
    thumbnailPath: '',
    folder_id: 'windows-folder',
    isTagged: false,
  },
  {
    id: 'posix-image',
    path: '/home/me/Pictures/Archive/forest.png',
    thumbnailPath: '',
    folder_id: 'posix-folder',
    isTagged: false,
  },
  {
    id: 'mixed-image',
    path: String.raw`C:\Users/me\Pictures/Trips\Moonrise.JPEG`,
    thumbnailPath: '',
    folder_id: 'mixed-folder',
    isTagged: false,
  },
  {
    id: 'filename-image',
    path: '/home/me/Pictures/Trips/Vacation-notes.jpg',
    thumbnailPath: '',
    folder_id: 'filename-folder',
    isTagged: false,
  },
];

const renderDialog = async (
  availableImages: Image[] = images,
  onClose = jest.fn(),
): Promise<ReturnType<typeof render>> => {
  mockFetchAllImages.mockResolvedValue({
    success: true,
    data: availableImages,
  });
  const result = render(
    <AddImagesToAlbumDialog
      isOpen={true}
      onClose={onClose}
      albumId="album-1"
      albumName="Trip"
    />,
  );

  await waitFor(() =>
    expect(screen.getAllByRole('button', { pressed: false })).toHaveLength(
      availableImages.length,
    ),
  );
  return result;
};

describe('AddImagesToAlbumDialog filename search', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAddImagesToAlbum.mockResolvedValue({ success: true });
  });

  it.each([
    { pathType: 'Windows', query: 'SuNsEt.JpG', filename: 'sunset.jpg' },
    { pathType: 'POSIX', query: 'FOREST.PNG', filename: 'forest.png' },
    {
      pathType: 'mixed-separator',
      query: 'oNrIsE.jPe',
      filename: 'Moonrise.JPEG',
    },
  ])(
    'matches only the $pathType filename regardless of case',
    async ({ query, filename }) => {
      const user = userEvent.setup();
      await renderDialog();

      await user.type(screen.getByPlaceholderText('Search images...'), query);

      expect(
        screen.getByRole('button', { name: filename }),
      ).toBeInTheDocument();
      expect(screen.getAllByRole('button', { pressed: false })).toHaveLength(1);
      expect(
        screen.queryByRole('button', { name: 'Vacation-notes.jpg' }),
      ).not.toBeInTheDocument();
    },
  );

  it('excludes a Windows image when only its parent directory matches', async () => {
    const user = userEvent.setup();
    await renderDialog([images[0]]);
    expect(
      screen.getByRole('button', { name: 'sunset.jpg' }),
    ).toBeInTheDocument();

    await user.type(
      screen.getByPlaceholderText('Search images...'),
      'vacation',
    );

    expect(
      screen.queryByRole('button', { name: 'sunset.jpg' }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText('No images found matching your search'),
    ).toBeInTheDocument();
  });

  it('keeps a basename match while excluding a matching Windows directory', async () => {
    const user = userEvent.setup();
    await renderDialog();

    await user.type(
      screen.getByPlaceholderText('Search images...'),
      'VaCaTiOn',
    );

    expect(
      screen.getByRole('button', { name: 'Vacation-notes.jpg' }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'sunset.jpg' }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByRole('button', { pressed: false })).toHaveLength(1);
  });

  it('excludes a POSIX image when only its parent directory matches', async () => {
    const user = userEvent.setup();
    await renderDialog([images[1]]);
    expect(
      screen.getByRole('button', { name: 'forest.png' }),
    ).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText('Search images...'), 'archive');

    expect(
      screen.queryByRole('button', { name: 'forest.png' }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText('No images found matching your search'),
    ).toBeInTheDocument();
  });

  it('searches the native filename when a POSIX name contains a backslash', async () => {
    const user = userEvent.setup();
    const name = String.raw`Summer\2024.jpg`;
    await renderDialog([
      {
        id: 'posix-backslash-image',
        path: `/home/me/Pictures/Trips/${name}`,
        thumbnailPath: '',
        folder_id: 'posix-backslash-folder',
        isTagged: false,
        metadata: {
          name,
          date_created: null,
          width: 100,
          height: 100,
          file_location: `/home/me/Pictures/Trips/${name}`,
          file_size: 1024,
          item_type: 'image',
        },
      },
    ]);

    await user.type(screen.getByPlaceholderText('Search images...'), 'SUMMER');

    expect(screen.getByRole('button', { name })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { pressed: false })).toHaveLength(1);
  });

  it('restores images after clearing and submits a selected search result', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    await renderDialog(images, onClose);
    const search = screen.getByPlaceholderText('Search images...');

    await user.type(search, 'SUNSET');
    expect(screen.getAllByRole('button', { pressed: false })).toHaveLength(1);

    await user.clear(search);
    for (const filename of [
      'sunset.jpg',
      'forest.png',
      'Moonrise.JPEG',
      'Vacation-notes.jpg',
    ]) {
      expect(
        screen.getByRole('button', { name: filename }),
      ).toBeInTheDocument();
    }
    expect(screen.getAllByRole('button', { pressed: false })).toHaveLength(
      images.length,
    );

    await user.type(search, 'SUNSET');
    const image = screen.getByRole('button', { name: 'sunset.jpg' });
    expect(image).toHaveAttribute('aria-pressed', 'false');
    await user.click(image);
    expect(image).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('1 image selected')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Add 1 Image' }));

    await waitFor(() =>
      expect(mockAddImagesToAlbum).toHaveBeenCalledWith('album-1', {
        image_ids: ['windows-image'],
      }),
    );
    expect(mockAddImagesToAlbum).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
  });
});
