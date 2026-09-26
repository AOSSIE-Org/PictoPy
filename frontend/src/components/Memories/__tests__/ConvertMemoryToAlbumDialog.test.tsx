import userEvent from '@testing-library/user-event';
import { render, screen } from '@/test-utils';
import type { MemoryCard } from '@/api/api-functions/memories';
import { ConvertMemoryToAlbumDialog } from '../ConvertMemoryToAlbumDialog';

jest.mock('@/api/api-functions', () => ({
  createAlbumFromMemory: jest.fn(),
}));

const memory = {
  memory_id: 'mem-1',
  title: 'Beach',
  subtitle: '26 July 2024',
  image_count: 4,
  video_count: 0,
} as MemoryCard;

const renderDialog = (isOpen: boolean) =>
  render(
    <ConvertMemoryToAlbumDialog
      memory={memory}
      isOpen={isOpen}
      onClose={jest.fn()}
    />,
  );

const nameInput = () => screen.getByLabelText(/album name/i);

describe('ConvertMemoryToAlbumDialog', () => {
  it('prefills the name from the memory title', () => {
    renderDialog(true);

    expect(nameInput()).toHaveValue('Beach');
  });

  // The parent happens to null the memory between opens, but the dialog must
  // not depend on that: reopening for the same memory has to start clean.
  it('clears a typed name when reopened for the same memory', async () => {
    const user = userEvent.setup();
    const { rerender } = renderDialog(true);

    await user.clear(nameInput());
    await user.type(nameInput(), 'Something else');
    expect(nameInput()).toHaveValue('Something else');

    rerender(
      <ConvertMemoryToAlbumDialog
        memory={memory}
        isOpen={false}
        onClose={jest.fn()}
      />,
    );
    rerender(
      <ConvertMemoryToAlbumDialog
        memory={memory}
        isOpen={true}
        onClose={jest.fn()}
      />,
    );

    expect(nameInput()).toHaveValue('Beach');
  });
});
