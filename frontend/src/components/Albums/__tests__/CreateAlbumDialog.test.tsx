import { render, screen } from '@testing-library/react';
import { CreateAlbumDialog } from '../CreateAlbumDialog';

describe('CreateAlbumDialog', () => {
  it('displays updated photo-only copy and does not mention videos', () => {
    render(<CreateAlbumDialog open={true} />);

    // Assert that the dialog description correctly states photo organization
    expect(
      screen.getByText('Create a new album to organize your photos.'),
    ).toBeInTheDocument();

    // Assert that "videos" is not mentioned anywhere in the dialog text content
    expect(screen.queryByText(/videos/i)).not.toBeInTheDocument();
  });
});
