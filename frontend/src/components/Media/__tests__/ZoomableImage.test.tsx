import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode, Ref } from 'react';
import { ZoomableImage } from '../ZoomableImage';

const mockSetTransform = jest.fn();
const mockZoomIn = jest.fn();
const mockZoomOut = jest.fn();
const mockTransformState = {
  scale: 1,
  positionX: 0,
  positionY: 0,
};

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

jest.mock('react-zoom-pan-pinch', () => {
  const React = require('react');

  const TransformWrapper = React.forwardRef(
    ({ children }: { children: ReactNode }, ref: Ref<unknown>) => {
      React.useImperativeHandle(ref, () => ({
        instance: {
          wrapperComponent: null,
          transformState: mockTransformState,
        },
        setTransform: mockSetTransform,
        zoomIn: mockZoomIn,
        zoomOut: mockZoomOut,
      }));

      return React.createElement(
        'div',
        { 'data-testid': 'transform-wrapper' },
        children,
      );
    },
  );

  const TransformComponent = ({ children }: { children: ReactNode }) =>
    React.createElement('div', null, children);

  return {
    TransformWrapper,
    TransformComponent,
  };
});

const mockElementRect = (
  element: Element,
  rect: Partial<DOMRect>,
  dimensions?: { clientWidth?: number; clientHeight?: number },
) => {
  Object.defineProperty(element, 'getBoundingClientRect', {
    configurable: true,
    value: () =>
      ({
        left: 0,
        top: 0,
        right: rect.width ?? 0,
        bottom: rect.height ?? 0,
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        toJSON: () => undefined,
        ...rect,
      }) as DOMRect,
  });

  if (dimensions?.clientWidth !== undefined) {
    Object.defineProperty(element, 'clientWidth', {
      configurable: true,
      value: dimensions.clientWidth,
    });
  }

  if (dimensions?.clientHeight !== undefined) {
    Object.defineProperty(element, 'clientHeight', {
      configurable: true,
      value: dimensions.clientHeight,
    });
  }
};

describe('ZoomableImage wheel behavior', () => {
  beforeEach(() => {
    mockSetTransform.mockClear();
    mockZoomIn.mockClear();
    mockZoomOut.mockClear();
    mockTransformState.scale = 1;
    mockTransformState.positionX = 0;
    mockTransformState.positionY = 0;
  });

  test('intercepts wheel zoom from the stable container when the transform wrapper is not ready', () => {
    const { container } = render(
      <ZoomableImage
        imagePath="/tmp/photo.jpg"
        alt="test image"
        rotation={0}
      />,
    );

    const wheelArea = container.firstElementChild as HTMLElement;
    const image = screen.getByAltText('test image');

    mockElementRect(
      wheelArea,
      { width: 800, height: 600, left: 0, top: 0 },
      { clientWidth: 800, clientHeight: 600 },
    );
    mockElementRect(
      image,
      { width: 200, height: 100, left: 100, top: 100 },
      { clientWidth: 200, clientHeight: 100 },
    );

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 750,
      clientY: 550,
    });

    expect(mockSetTransform).toHaveBeenCalledWith(290, 245, 1.1, 0);
  });
});
