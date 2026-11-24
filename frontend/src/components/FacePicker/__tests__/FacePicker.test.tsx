import { render, screen, fireEvent } from '@testing-library/react';
import { FacePicker } from '../FacePicker';
import { MAX_SELECTED_FACES } from '@/utils/faceSearch';

const makeFaces = (count: number) =>
  Array.from({ length: count }, (_, index) => ({
    index,
    bbox: { x: index * 100, y: 50, width: 80, height: 80 },
    confidence: 0.9,
  }));

const setup = (count = 3, facesSkipped = 0) => {
  const onSearch = jest.fn();
  render(
    <FacePicker
      imageSrc="/photo.jpg"
      faces={makeFaces(count)}
      imageWidth={1000}
      imageHeight={500}
      facesSkipped={facesSkipped}
      onSearch={onSearch}
    />,
  );
  return onSearch;
};

const face = (n: number) => screen.getByRole('button', { name: `Face ${n}` });
const searchButton = () => screen.getByRole('button', { name: /^Search/ });

describe('FacePicker', () => {
  test('draws one numbered box per face, placed by percentage', () => {
    setup(2);

    expect(face(1)).toHaveStyle({
      left: '0%',
      top: '10%',
      width: '8%',
      height: '16%',
    });
    expect(face(2)).toHaveStyle({ left: '10%' });
  });

  test('numbers faces from left to right, not in detector order', () => {
    const onSearch = jest.fn();
    // The detector found the rightmost face first.
    const faces = [
      {
        index: 0,
        bbox: { x: 800, y: 50, width: 80, height: 80 },
        confidence: 0.9,
      },
      {
        index: 1,
        bbox: { x: 100, y: 50, width: 80, height: 80 },
        confidence: 0.8,
      },
      {
        index: 2,
        bbox: { x: 450, y: 50, width: 80, height: 80 },
        confidence: 0.7,
      },
    ];
    render(
      <FacePicker
        imageSrc="/photo.jpg"
        faces={faces}
        imageWidth={1000}
        imageHeight={500}
        facesSkipped={0}
        onSearch={onSearch}
      />,
    );

    expect(face(1)).toHaveStyle({ left: '10%' });
    expect(face(2)).toHaveStyle({ left: '45%' });
    expect(face(3)).toHaveStyle({ left: '80%' });

    // Picking "Face 3" (rightmost) still sends the detector's index 0.
    fireEvent.click(face(3));
    fireEvent.click(searchButton());
    expect(onSearch).toHaveBeenCalledWith([0], 'match_any');
  });

  test('numbers a grid of photos row by row', () => {
    // Two rows of three, handed over in a scrambled detector order.
    const at = (index: number, x: number, y: number) => ({
      index,
      bbox: { x, y, width: 80, height: 80 },
      confidence: 0.9,
    });
    const faces = [
      at(0, 100, 300), // bottom left
      at(1, 100, 50), // top left
      at(2, 450, 300), // bottom middle
      at(3, 450, 50), // top middle
      at(4, 800, 300), // bottom right
      at(5, 800, 50), // top right
    ];
    render(
      <FacePicker
        imageSrc="/photo.jpg"
        faces={faces}
        imageWidth={1000}
        imageHeight={500}
        facesSkipped={0}
        onSearch={jest.fn()}
      />,
    );

    const left = (n: number) => ({ top: '10%', left: `${n}%` });
    expect(face(1)).toHaveStyle(left(10));
    expect(face(2)).toHaveStyle(left(45));
    expect(face(3)).toHaveStyle(left(80));
    expect(face(4)).toHaveStyle({ top: '60%', left: '10%' });
    expect(face(6)).toHaveStyle({ top: '60%', left: '80%' });
  });

  test('Search is disabled until a face is picked', () => {
    setup();
    expect(searchButton()).toBeDisabled();

    fireEvent.click(face(1));

    expect(searchButton()).toBeEnabled();
    expect(searchButton()).toHaveTextContent('Search (1)');
  });

  test('clicking a picked face again unpicks it', () => {
    setup();
    fireEvent.click(face(1));
    expect(face(1)).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(face(1));

    expect(face(1)).toHaveAttribute('aria-pressed', 'false');
    expect(searchButton()).toBeDisabled();
  });

  test('sends the picked indices in order, with match_any by default', () => {
    const onSearch = setup();

    fireEvent.click(face(3));
    fireEvent.click(face(1));
    fireEvent.click(searchButton());

    expect(onSearch).toHaveBeenCalledWith([0, 2], 'match_any');
  });

  test('the any/all switch only appears once two faces are picked', () => {
    setup();
    fireEvent.click(face(1));
    expect(screen.queryByRole('switch')).not.toBeInTheDocument();

    fireEvent.click(face(2));

    expect(screen.getByRole('switch')).toBeInTheDocument();
  });

  test('sends match_all when the switch is turned on', () => {
    const onSearch = setup();
    fireEvent.click(face(1));
    fireEvent.click(face(2));

    fireEvent.click(screen.getByRole('switch'));
    fireEvent.click(searchButton());

    expect(onSearch).toHaveBeenCalledWith([0, 1], 'match_all');
  });

  test('stops at the selection limit and explains why', () => {
    setup(MAX_SELECTED_FACES + 1);
    for (let n = 1; n <= MAX_SELECTED_FACES; n++) fireEvent.click(face(n));

    const extra = face(MAX_SELECTED_FACES + 1);
    expect(extra).toBeDisabled();
    expect(
      screen.getByText(
        `You can pick up to ${MAX_SELECTED_FACES} faces at a time.`,
      ),
    ).toBeInTheDocument();

    fireEvent.click(face(1));
    expect(extra).toBeEnabled();
  });

  test('mentions faces that were too small to use', () => {
    setup(2, 1);
    expect(
      screen.getByText('1 more face was too small or blurry to use.'),
    ).toBeInTheDocument();
  });

  test('uses the plural when several faces were skipped', () => {
    setup(2, 3);
    expect(
      screen.getByText('3 more faces were too small or blurry to use.'),
    ).toBeInTheDocument();
  });

  test('says nothing about skipped faces when none were', () => {
    setup(2, 0);
    expect(screen.queryByText(/too small or blurry/)).not.toBeInTheDocument();
  });

  test('shows a message instead of boxes when the photo cannot load', () => {
    setup(2);

    fireEvent.error(screen.getByAltText('Photo to search with'));

    expect(
      screen.getByText('This photo could not be shown.'),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Face 1' }),
    ).not.toBeInTheDocument();
  });
});
