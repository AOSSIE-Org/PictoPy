import userEvent from '@testing-library/user-event';
import { render, screen } from '@/test-utils';
import type { MemoryCard as MemoryCardType } from '@/api/api-functions/memories';
import { MemoryCard } from '../MemoryCard';

jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
  convertFileSrc: jest.fn((path: string) => `asset://localhost/${path}`),
}));

const memory: MemoryCardType = {
  memory_id: 'mem-1',
  dedupe_key: 'import:2024-07-26..2024-07-26',
  event_type: 'import_event',
  status: 'complete',
  title: 'Beach',
  subtitle: '26 July 2024',
  place_label: null,
  center_lat: null,
  center_lon: null,
  surface_date: '2024-07-26',
  period_start: '2024-07-26T10:00:00',
  period_end: '2024-07-26T10:05:00',
  image_count: 4,
  video_count: 0,
  cover_image_id: null,
  cover_thumbnail_path: null,
  score: 1,
  notified_at: null,
  viewed_at: null,
  dismissed: false,
  created_at: '2024-07-26T12:00:00',
};

const renderCard = () => {
  const onOpen = jest.fn();
  const onConvertToAlbum = jest.fn();
  render(
    <MemoryCard
      memory={memory}
      onOpen={onOpen}
      onConvertToAlbum={onConvertToAlbum}
    />,
  );
  return { onOpen, onConvertToAlbum };
};

describe('MemoryCard', () => {
  it('opens the memory when the tile is clicked', async () => {
    const user = userEvent.setup();
    const { onOpen } = renderCard();

    await user.click(
      screen.getByRole('button', { name: 'Open memory: Beach' }),
    );

    expect(onOpen).toHaveBeenCalledWith('mem-1');
  });

  it('converts the memory from the actions menu without opening it', async () => {
    const user = userEvent.setup();
    const { onOpen, onConvertToAlbum } = renderCard();

    await user.click(screen.getByRole('button', { name: 'Options for Beach' }));
    await user.click(await screen.findByText('Convert to Album'));

    expect(onConvertToAlbum).toHaveBeenCalledWith('mem-1');
    // The menu is a sibling of the tile, not a child, so acting on it must
    // never open the story viewer.
    expect(onOpen).not.toHaveBeenCalled();
  });
});
