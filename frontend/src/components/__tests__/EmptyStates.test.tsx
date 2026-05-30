import { render, screen } from '@/test-utils';
import { EmptyGalleryState } from '../EmptyStates/EmptyGalleryState';
import { EmptyAITaggingState } from '../EmptyStates/EmptyAITaggingState';

describe('EmptyGalleryState', () => {
  test('renders heading', () => {
    render(<EmptyGalleryState />);

    expect(
      screen.getByRole('heading', { name: /no images to display/i }),
    ).toBeInTheDocument();
  });

  test('renders gallery instructions', () => {
    render(<EmptyGalleryState />);

    expect(
      screen.getByText(
        (_, element) =>
          element?.tagName === 'SPAN' &&
          element?.textContent === 'Go to Settings to add folders.',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/supports png, jpg, jpeg image formats/i),
    ).toBeInTheDocument();
  });
});

describe('EmptyAITaggingState', () => {
  test('renders heading', () => {
    render(<EmptyAITaggingState />);

    expect(
      screen.getByRole('heading', { name: /no ai tagged images/i }),
    ).toBeInTheDocument();
  });

  test('renders AI tagging instructions', () => {
    render(<EmptyAITaggingState />);

    expect(
      screen.getByText(/ai will automatically detect objects and people/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/supports png, jpg, jpeg image formats/i),
    ).toBeInTheDocument();
  });
});
