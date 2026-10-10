import userEvent from '@testing-library/user-event';
import { render, screen } from '@/test-utils';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Image } from '@/types/Media';
import { AddImagesToAlbumDialog } from '../AddImagesToAlbumDialog';

jest.mock('@/hooks/useQueryExtension', () => ({
  usePictoQuery: jest.fn(),
  usePictoMutation: jest.fn(),
}));

jest.mock('@/hooks/useMutationFeedback', () => ({
  useMutationFeedback: jest.fn(),
}));

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

const mockUsePictoQuery = usePictoQuery as jest.Mock;
const mockUsePictoMutation = usePictoMutation as jest.Mock;
const mockUseMutationFeedback = useMutationFeedback as jest.Mock;

const image = (path: string): Image => ({
  id: path,
  path,
  thumbnailPath: path,
  folder_id: 'f1',
  isTagged: false,
});

const renderDialog = (images: Image[]) => {
  mockUsePictoQuery.mockReturnValue({
    data: { data: images },
    isLoading: false,
  });
  mockUsePictoMutation.mockReturnValue({ mutate: jest.fn() });
  mockUseMutationFeedback.mockReturnValue(undefined);

  return render(
    <AddImagesToAlbumDialog
      isOpen={true}
      onClose={jest.fn()}
      albumId="a1"
      albumName="Trip"
    />,
  );
};

describe('AddImagesToAlbumDialog', () => {
  it('finds a Windows-path image by its filename, not the whole path', async () => {
    const user = userEvent.setup();
    renderDialog([image('C:\\Users\\me\\Pictures\\sunset.jpg')]);

    await user.type(screen.getByPlaceholderText(/search images/i), 'sunset');

    expect(
      screen.getByRole('button', { name: 'sunset.jpg' }),
    ).toBeInTheDocument();
  });

  it('does not match a Windows-path image by an unrelated folder segment', async () => {
    const user = userEvent.setup();
    renderDialog([image('C:\\Users\\me\\Pictures\\sunset.jpg')]);

    await user.type(screen.getByPlaceholderText(/search images/i), 'pictures');

    expect(
      screen.queryByRole('button', { name: 'sunset.jpg' }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/no images found matching your search/i),
    ).toBeInTheDocument();
  });
});
