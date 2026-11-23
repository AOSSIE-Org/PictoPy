import { screen, render } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { GalleryViewSelector } from '../GalleryViewSelector';

describe('GalleryViewSelector', () => {
  beforeEach(() => localStorage.clear());

  it('offers only Small, Medium and Large with Medium selected by default', async () => {
    const user = userEvent.setup();
    render(<GalleryViewSelector />);

    const trigger = screen.getByRole('button', { name: 'Thumbnail size' });
    await user.tab();
    expect(trigger).toHaveFocus();
    await user.keyboard('{ArrowDown}');

    expect(screen.queryByRole('menuitemradio', { name: /River/ })).toBeNull();
    expect(screen.queryByRole('menuitemradio', { name: /Square/ })).toBeNull();
    expect(screen.getAllByRole('menuitemradio')).toHaveLength(3);
    expect(screen.getByRole('menuitemradio', { name: /Small/ })).toBeTruthy();
    expect(
      screen.getByRole('menuitemradio', { name: /Medium/ }),
    ).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('menuitemradio', { name: /Large/ })).toBeTruthy();

    await user.keyboard('{Enter}');
    expect(
      JSON.parse(localStorage.getItem('pictopy-gallery-view') ?? 'null'),
    ).toEqual({
      size: 'small',
    });
  });
});
