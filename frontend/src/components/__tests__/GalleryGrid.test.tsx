import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { GalleryGrid } from '../GalleryGrid';
import { GalleryViewSelector } from '../GalleryViewSelector';

describe('GalleryGrid', () => {
  beforeEach(() => localStorage.clear());

  it('responds to shared view and size changes with a responsive minimum width', async () => {
    const user = userEvent.setup();
    render(
      <>
        <GalleryViewSelector />
        <GalleryGrid>Photo</GalleryGrid>
      </>,
    );

    const grid = document.querySelector('[data-gallery-size]');
    if (!(grid instanceof HTMLElement)) throw new Error('Gallery grid missing');
    expect(grid).toHaveAttribute('data-gallery-size', 'medium');
    expect(grid).toHaveStyle({ gap: '16px' });

    await user.click(screen.getByRole('button', { name: 'Thumbnail size' }));
    await user.click(screen.getByRole('menuitemradio', { name: /Small/ }));

    expect(grid).toHaveAttribute('data-gallery-size', 'small');
    expect(grid).toHaveStyle({ gap: '8px' });
    expect(grid.style.gridTemplateColumns).toContain('160px');

    await user.click(screen.getByRole('button', { name: 'Thumbnail size' }));
    await user.click(screen.getByRole('menuitemradio', { name: /Large/ }));

    expect(grid).toHaveAttribute('data-gallery-size', 'large');
    expect(grid).toHaveStyle({ gap: '24px' });
    expect(grid.style.gridTemplateColumns).toContain('288px');

    await user.click(screen.getByRole('button', { name: 'Thumbnail size' }));
    await user.click(screen.getByRole('menuitemradio', { name: /Medium/ }));

    expect(grid).toHaveAttribute('data-gallery-size', 'medium');
    expect(grid).toHaveStyle({ gap: '16px' });
    expect(grid.style.gridTemplateColumns).toContain('224px');
  });
});
