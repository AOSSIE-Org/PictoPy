import { render, screen, fireEvent } from '@testing-library/react';
import { FaceCrop } from '../FaceCrop';

const face = (x: number, y: number, size = 100) => ({
  index: 0,
  bbox: { x, y, width: size, height: size },
  confidence: 0.9,
});

describe('FaceCrop', () => {
  test('zooms the photo onto the face', () => {
    // A 100px face padded to a 150px square, inside a 1000x500 photo.
    render(
      <FaceCrop
        src="/p.jpg"
        face={face(400, 200)}
        imageWidth={1000}
        imageHeight={500}
      />,
    );

    const img = screen.getByAltText('Searched face');
    expect(img).toHaveStyle({
      width: `${(1000 / 150) * 100}%`,
      left: `${(-375 / 150) * 100}%`,
      top: `${(-175 / 150) * 100}%`,
    });
  });

  test('stays inside the photo for a face at the corner', () => {
    render(
      <FaceCrop
        src="/p.jpg"
        face={face(0, 0)}
        imageWidth={1000}
        imageHeight={500}
      />,
    );

    const img = screen.getByAltText('Searched face');
    expect(img.style.left).toBe('0%');
    expect(img.style.top).toBe('0%');
  });

  test('never crops a square bigger than the photo', () => {
    render(
      <FaceCrop
        src="/p.jpg"
        face={face(0, 0, 400)}
        imageWidth={500}
        imageHeight={300}
      />,
    );

    // side is capped at the shorter edge (300).
    expect(screen.getByAltText('Searched face')).toHaveStyle({
      width: `${(500 / 300) * 100}%`,
    });
  });

  test('reports a photo that fails to load', () => {
    const onError = jest.fn();
    render(
      <FaceCrop
        src="/missing.jpg"
        face={face(10, 10)}
        imageWidth={1000}
        imageHeight={500}
        onError={onError}
      />,
    );

    fireEvent.error(screen.getByAltText('Searched face'));

    expect(onError).toHaveBeenCalled();
  });
});
